import React from "react";
import { Link, useLocation } from "react-router-dom";
import { MapPin } from "lucide-react";

function NavMenu() {
  const { pathname } = useLocation();

  return (
    <nav
      role="navigation"
      aria-label="Main navigation"
      className="fixed top-0 inset-x-0 z-50 h-14 bg-white/95 backdrop-blur-sm border-b border-linen-200 flex items-center px-6"
    >
      <Link
        to="/"
        className="flex items-center gap-2.5 font-serif text-xl text-ink-900 hover:text-bronze-500 transition-colors"
        aria-label="Estates home"
      >
        <MapPin size={17} className="text-bronze-500" strokeWidth={1.5} />
        <span>Estates</span>
      </Link>

      <div className="ml-auto flex items-center gap-6">
        <Link
          to="/"
          className={`font-sans text-sm transition-colors ${
            pathname === "/"
              ? "text-ink-900 font-medium"
              : "text-ink-400 hover:text-ink-900"
          }`}
        >
          Map
        </Link>
        <Link
          to="/cache-inspector"
          className={`font-sans text-sm transition-colors ${
            pathname === "/cache-inspector"
              ? "text-ink-900 font-medium"
              : "text-ink-400 hover:text-ink-900"
          }`}
        >
          Cache
        </Link>
      </div>
    </nav>
  );
}

export default NavMenu;
