"use client";

import React, { useState } from "react";
import Link from "next/link";
import { GarudaLogo } from "@/components/brand/GarudaLogo";
import { Button } from "@/components/ui/button";
import { ShieldCheck, Menu, X, ArrowRight, User } from "lucide-react";
import { useAuth } from "@/lib/auth";

export function MarketingNav() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user } = useAuth();

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/80 bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-2 group">
          <GarudaLogo size={32} showWordmark={true} subtitle="DEFENSE ENGINE" />
        </Link>

        {/* Desktop Navigation Links */}
        <nav className="hidden md:flex items-center gap-6 text-sm text-muted-foreground font-medium">
          <Link
            href="#how-it-works"
            className="hover:text-foreground transition-colors hover:text-white"
          >
            How It Works
          </Link>
          <Link
            href="#multimodal"
            className="hover:text-foreground transition-colors hover:text-white"
          >
            Capabilities
          </Link>
          <Link
            href="#qr-upi"
            className="hover:text-foreground transition-colors hover:text-white"
          >
            QR & UPI
          </Link>
          <Link
            href="#explainable-risk"
            className="hover:text-foreground transition-colors hover:text-white"
          >
            Explainable Risk
          </Link>
          <Link
            href="#reporting"
            className="hover:text-foreground transition-colors hover:text-white"
          >
            Reporting
          </Link>
          <Link
            href="#privacy"
            className="hover:text-foreground transition-colors hover:text-white"
          >
            Privacy
          </Link>
        </nav>

        {/* Action Buttons */}
        <div className="hidden md:flex items-center gap-3">
          {user ? (
            <Button asChild variant="outline" size="sm" className="gap-2">
              <Link href="/dashboard">
                <User className="w-3.5 h-3.5 text-primary" />
                Console
              </Link>
            </Button>
          ) : (
            <Button asChild variant="ghost" size="sm">
              <Link href="/login">Sign In</Link>
            </Button>
          )}

          <Button asChild size="sm" className="gap-2 shadow-sm font-medium">
            <Link href="/message-analyzer">
              <ShieldCheck className="w-4 h-4" />
              Analyze a Threat
            </Link>
          </Button>
        </div>

        {/* Mobile Menu Button */}
        <div className="flex md:hidden">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </Button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-border bg-surface px-4 py-5 space-y-4">
          <nav className="flex flex-col space-y-3 text-sm font-medium">
            <Link
              href="#how-it-works"
              onClick={() => setMobileMenuOpen(false)}
              className="text-muted-foreground hover:text-white py-1"
            >
              How It Works
            </Link>
            <Link
              href="#multimodal"
              onClick={() => setMobileMenuOpen(false)}
              className="text-muted-foreground hover:text-white py-1"
            >
              Capabilities
            </Link>
            <Link
              href="#qr-upi"
              onClick={() => setMobileMenuOpen(false)}
              className="text-muted-foreground hover:text-white py-1"
            >
              QR & UPI Defense
            </Link>
            <Link
              href="#explainable-risk"
              onClick={() => setMobileMenuOpen(false)}
              className="text-muted-foreground hover:text-white py-1"
            >
              Explainable Risk
            </Link>
            <Link
              href="#reporting"
              onClick={() => setMobileMenuOpen(false)}
              className="text-muted-foreground hover:text-white py-1"
            >
              Incident Reporting
            </Link>
            <Link
              href="#privacy"
              onClick={() => setMobileMenuOpen(false)}
              className="text-muted-foreground hover:text-white py-1"
            >
              Privacy & Security
            </Link>
          </nav>
          <div className="pt-3 border-t border-border flex flex-col gap-2">
            <Button asChild variant="outline" className="w-full justify-center">
              <Link href="/login" onClick={() => setMobileMenuOpen(false)}>
                Sign In
              </Link>
            </Button>
            <Button asChild className="w-full justify-center gap-2">
              <Link href="/message-analyzer" onClick={() => setMobileMenuOpen(false)}>
                Analyze a Threat
                <ArrowRight className="w-4 h-4" />
              </Link>
            </Button>
          </div>
        </div>
      )}
    </header>
  );
}
