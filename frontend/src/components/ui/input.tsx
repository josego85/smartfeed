import { cn } from "@/lib/utils";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  icon?: React.ReactNode;
}

export function Input({ className, icon, ...props }: InputProps) {
  if (icon) {
    return (
      <div className="relative">
        <div className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-slate-400">
          {icon}
        </div>
        <input
          className={cn(
            "w-full rounded-lg border border-slate-200 bg-white py-2.5 pl-10 pr-4 text-sm",
            "placeholder:text-slate-400 focus:border-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-100",
            className,
          )}
          {...props}
        />
      </div>
    );
  }

  return (
    <input
      className={cn(
        "w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm",
        "placeholder:text-slate-400 focus:border-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-100",
        className,
      )}
      {...props}
    />
  );
}
