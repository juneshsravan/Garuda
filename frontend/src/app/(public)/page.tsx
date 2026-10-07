import React from "react";
import { MarketingNav } from "@/components/layout/MarketingNav";
import { HeroSection } from "@/components/landing/HeroSection";
import { ConsolePreview } from "@/components/landing/ConsolePreview";
import { HowItWorksSection } from "@/components/landing/HowItWorksSection";
import { MultimodalSection } from "@/components/landing/MultimodalSection";
import { QrUpiSection } from "@/components/landing/QrUpiSection";
import { ExplainableRiskSection } from "@/components/landing/ExplainableRiskSection";
import { HistorySection } from "@/components/landing/HistorySection";
import { ReportingSection } from "@/components/landing/ReportingSection";
import { PrivacySection } from "@/components/landing/PrivacySection";
import { FinalCtaSection } from "@/components/landing/FinalCtaSection";
import { Footer } from "@/components/landing/Footer";

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col bg-background selection:bg-primary/30 selection:text-white">
      {/* Top marketing nav ONLY on the landing page */}
      <MarketingNav />

      <main className="flex-1">
        {/* Hero Section */}
        <HeroSection />

        {/* Security Console Live Preview */}
        <section className="px-4 sm:px-6 lg:px-8 pb-20 sm:pb-28 -mt-6 sm:-mt-10">
          <ConsolePreview />
        </section>

        {/* 1. How GARUDA Works */}
        <HowItWorksSection />

        {/* 2. Multimodal Detection */}
        <MultimodalSection />

        {/* 3. QR & UPI Protection */}
        <QrUpiSection />

        {/* 4. Explainable Risk */}
        <ExplainableRiskSection />

        {/* 5. History */}
        <HistorySection />

        {/* 6. Reporting */}
        <ReportingSection />

        {/* 7. Privacy & Security */}
        <PrivacySection />

        {/* 8. Final CTA */}
        <FinalCtaSection />
      </main>

      {/* 9. Footer */}
      <Footer />
    </div>
  );
}
