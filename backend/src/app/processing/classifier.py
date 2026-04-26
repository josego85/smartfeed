import numpy as np

from ..core.config import settings
from .embeddings import embed, embed_batch

# Rich keyword descriptions improve zero-shot accuracy significantly.
# The model compares article embeddings against these, not just the short label.
_TOPIC_DESCRIPTIONS: dict[str, str] = {
    "Artificial Intelligence & Machine Learning": (
        "artificial intelligence machine learning deep learning neural network large language model "
        "LLM GPT ChatGPT OpenAI Anthropic Claude Gemini Llama model training transformer "
        "NLP natural language processing computer vision AI research foundation model "
        "diffusion model reinforcement learning AI assistant benchmark fine-tuning"
    ),
    "Web Development & Frontend": (
        "web development frontend backend JavaScript TypeScript React Vue Angular CSS HTML "
        "Next.js Tailwind REST API GraphQL Node.js web framework browser UI design UX "
        "web performance SPA server-side rendering full stack developer web app"
    ),
    "DevOps & Infrastructure": (
        "DevOps infrastructure cloud computing AWS Azure Google Cloud Kubernetes Docker container "
        "CI CD pipeline deployment monitoring Terraform Ansible SRE reliability scalability "
        "microservices serverless platform engineering GitOps observability logging"
    ),
    "Programming Languages & Tooling": (
        "programming language Python Go Rust Java C++ Swift Kotlin compiler interpreter "
        "IDE developer tools package manager SDK framework software engineering code quality "
        "testing debugging refactoring software architecture design patterns API library"
    ),
    "Cybersecurity": (
        "cybersecurity information security hacking data breach ransomware malware phishing "
        "network security vulnerability CVE zero-day encryption penetration testing "
        "CISO threat intelligence exploit firewall authentication privacy GDPR attack defense"
    ),
    "Open Source & Linux": (
        "open source Linux GitHub free software GPL license open source project "
        "Linux distribution Ubuntu Debian Fedora kernel bash community software "
        "git repository contribution fork pull request open source maintainer"
    ),
    "Hardware & Electronics": (
        "hardware electronics CPU GPU processor chip semiconductor FPGA embedded systems "
        "IoT Internet of Things Arduino Raspberry Pi circuit PCB electronics engineering "
        "Intel AMD ARM RISC-V robotics 3D printing sensors microcontroller"
    ),
    "Science & Research": (
        "science research scientific study academic paper physics biology chemistry "
        "mathematics quantum computing space astronomy neuroscience genomics "
        "climate science technology research innovation breakthrough experiment peer review"
    ),
}

_topic_embeddings: dict[str, list[float]] = {}


def _description_for(topic: str) -> str:
    return _TOPIC_DESCRIPTIONS.get(topic, topic)


def _load_topic_embeddings() -> dict[str, list[float]]:
    global _topic_embeddings
    if not _topic_embeddings:
        descriptions = [_description_for(t) for t in settings.topics]
        vectors = embed_batch(descriptions)
        _topic_embeddings = dict(zip(settings.topics, vectors))
    return _topic_embeddings


def classify(text: str) -> str:
    # Use only first 500 chars — full content dilutes the classification signal.
    truncated = text[:500]
    article_vec = np.array(embed(truncated))
    topic_vecs = _load_topic_embeddings()

    best_topic = settings.topics[0]
    best_score = -1.0

    for topic, vec in topic_vecs.items():
        topic_vec = np.array(vec)
        score = float(
            np.dot(article_vec, topic_vec)
            / (np.linalg.norm(article_vec) * np.linalg.norm(topic_vec))
        )
        if score > best_score:
            best_score = score
            best_topic = topic

    return best_topic
