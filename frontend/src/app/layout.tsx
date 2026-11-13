import type { ReactNode } from "react";

export default async function RootLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ locale?: string }>;
}) {
  const { locale } = await params;

  return (
    <html lang={locale ?? "en"}>
      <body>{children}</body>
    </html>
  );
}
