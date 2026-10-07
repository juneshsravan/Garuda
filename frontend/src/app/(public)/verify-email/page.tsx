"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { GarudaLogo } from "@/components/brand/GarudaLogo";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { verifyEmailSchema, VerifyEmailFormData } from "@/lib/validations/auth";
import { MailCheck, AlertCircle, CheckCircle2, Loader2, RefreshCw, ArrowRight } from "lucide-react";

export default function VerifyEmailPage() {
  const router = useRouter();
  const [countdown, setCountdown] = useState<number>(0);
  const [resendStatus, setResendStatus] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [verifiedSuccess, setVerifiedSuccess] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<VerifyEmailFormData>({
    resolver: zodResolver(verifyEmailSchema),
    defaultValues: {
      email: "",
      code: "",
    },
  });

  const emailValue = watch("email");

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (countdown > 0) {
      timer = setTimeout(() => setCountdown(countdown - 1), 1000);
    }
    return () => clearTimeout(timer);
  }, [countdown]);

  const onVerify = async (data: VerifyEmailFormData) => {
    setApiError(null);
    setIsSubmitting(true);

    try {
      // MOCK: Built against ARCHITECTURE Section 6 POST /api/auth/verify-email
      await new Promise((resolve) => setTimeout(resolve, 800));

      if (data.code === "000000") {
        setApiError("Invalid or expired verification code (5 attempts allowed).");
        setIsSubmitting(false);
        return;
      }

      setVerifiedSuccess(true);
      setIsSubmitting(false);
      setTimeout(() => {
        router.push("/login");
      }, 2000);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Verification request failed.";
      setApiError(message);
      setIsSubmitting(false);
    }
  };

  const handleResendCode = async () => {
    if (!emailValue || errors.email) {
      setApiError("Please enter your registered email address first.");
      return;
    }

    setApiError(null);
    setResendStatus("Dispatching new code...");

    // MOCK: Built against ARCHITECTURE Section 6 POST /api/auth/resend-code (1/min limit)
    setTimeout(() => {
      setResendStatus("A fresh 6-digit verification code has been dispatched.");
      setCountdown(60); // 60s cooldown
    }, 700);
  };

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-background relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,#0d1424,transparent_70%)] pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10 text-center px-4">
        <Link href="/" className="inline-flex justify-center mb-4 group">
          <GarudaLogo size={48} showWordmark={true} wordmarkClassName="text-xl" subtitle="CYBER DEFENSE PLATFORM" />
        </Link>
        <h2 className="font-mono text-2xl font-bold tracking-tight text-white mt-2">
          Verify Email Address
        </h2>
        <p className="text-xs text-muted-foreground mt-1">
          Enter the 6-digit authorization code dispatched to your inbox.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4 relative z-10">
        <div className="rounded-xl border border-border bg-surface p-6 sm:p-8 shadow-xl">
          {verifiedSuccess ? (
            <div className="text-center py-6 space-y-3">
              <div className="w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <h3 className="font-mono text-base font-bold text-white">
                Email Successfully Verified
              </h3>
              <p className="text-xs text-muted-foreground">
                Your credentials are active. Redirecting to security console sign in...
              </p>
            </div>
          ) : (
            <>
              {apiError && (
                <div className="mb-5 p-3 rounded-lg border border-destructive/30 bg-destructive/10 text-destructive text-xs font-mono flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{apiError}</span>
                </div>
              )}

              {resendStatus && (
                <div className="mb-5 p-3 rounded-lg border border-accent-cyan/30 bg-accent-cyan/10 text-accent-cyan text-xs font-mono flex items-center gap-2">
                  <MailCheck className="w-4 h-4 shrink-0" />
                  <span>{resendStatus}</span>
                </div>
              )}

              <form onSubmit={handleSubmit(onVerify)} className="space-y-4">
                {/* Email Address */}
                <div>
                  <label
                    htmlFor="email"
                    className="block text-xs font-mono font-medium text-slate-300 mb-1.5"
                  >
                    REGISTERED EMAIL
                  </label>
                  <Input
                    id="email"
                    type="email"
                    autoComplete="email"
                    placeholder="analyst@organization.in"
                    error={!!errors.email}
                    {...register("email")}
                  />
                  {errors.email && (
                    <p className="text-[11px] font-mono text-destructive mt-1">
                      {errors.email.message}
                    </p>
                  )}
                </div>

                {/* 6-digit Code */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label
                      htmlFor="code"
                      className="block text-xs font-mono font-medium text-slate-300"
                    >
                      6-DIGIT VERIFICATION CODE
                    </label>
                    <span className="text-[11px] font-mono text-muted-foreground">
                      Valid for 10 min
                    </span>
                  </div>

                  <Input
                    id="code"
                    type="text"
                    inputMode="numeric"
                    maxLength={6}
                    placeholder="482910"
                    className="font-mono text-center tracking-widest text-lg h-12"
                    error={!!errors.code}
                    {...register("code")}
                  />
                  {errors.code && (
                    <p className="text-[11px] font-mono text-destructive mt-1">
                      {errors.code.message}
                    </p>
                  )}
                </div>

                {/* Verify Button */}
                <div className="pt-2">
                  <Button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full gap-2 font-medium h-10"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Verifying Code...
                      </>
                    ) : (
                      <>
                        Confirm Code
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </Button>
                </div>
              </form>

              {/* Resend Code Section */}
              <div className="mt-6 pt-5 border-t border-border/80 flex items-center justify-between text-xs text-muted-foreground font-mono">
                <span>Didn&apos;t get a code?</span>
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={countdown > 0}
                  onClick={handleResendCode}
                  className="gap-1.5 text-xs text-primary hover:text-accent-cyan p-0 h-auto"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${countdown > 0 ? "animate-spin" : ""}`} />
                  {countdown > 0 ? `Resend in ${countdown}s` : "Resend Code"}
                </Button>
              </div>
            </>
          )}

          {/* Back to Login */}
          <div className="mt-6 pt-4 border-t border-border/60 text-center text-xs text-muted-foreground">
            <Link
              href="/login"
              className="text-muted-foreground hover:text-white font-mono transition-colors"
            >
              ← Back to Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
