import Link from "next/link";

type PageHeaderProps = {
  eyebrow?: string;
  title: string;
  description: string;
};

export default function PageHeader({
  eyebrow = "ANASTARIA",
  title,
  description,
}: PageHeaderProps) {
  return (
    <header className="max-w-3xl">
      <Link
        href="/"
        className="text-sm text-gray-500 transition hover:text-white"
      >
        ← Back to ANASTARIA
      </Link>

      <div className="mt-12">
        <p className="text-xs font-bold uppercase tracking-[0.35em] text-amber-400">
          {eyebrow}
        </p>

        <h1 className="mt-3 text-5xl font-black tracking-tight text-white sm:text-6xl">
          {title}
        </h1>

        <p className="mt-5 text-base leading-8 text-gray-500 sm:text-lg">
          {description}
        </p>
      </div>
    </header>
  );
}
