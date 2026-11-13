"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
export function Navigation() {
  const path = usePathname();
  return <nav aria-label="Navegação principal" className="flex flex-wrap gap-1 md:flex-col md:gap-2">{[{ href: "/dashboard", label: "Dashboard" }, { href: "/units", label: "Unidades" }, { href: "/employees", label: "Colaboradoras" }].map(item => <Link key={item.href} href={item.href} aria-current={path === item.href || path.startsWith(`${item.href}/`) ? "page" : undefined} className="rounded-xl px-2 py-3 text-sm font-medium transition hover:bg-white/10 aria-[current=page]:bg-white/15 aria-[current=page]:text-white focus-visible:outline-2 focus-visible:outline-white md:px-4">{item.label}</Link>)}</nav>;
}
