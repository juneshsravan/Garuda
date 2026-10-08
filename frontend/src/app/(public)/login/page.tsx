"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { GarudaLogo } from "@/components/brand/GarudaLogo";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { LoadingState } from "@/components/ui/states";
import { loginSchema, LoginFormData } from "@/lib/validations/auth";
import { Eye, EyeOff, AlertCircle, Loader2, ArrowRight } from "lucide-react";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const { login, user, isLoading } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Route guard: /login redirects to /dashboard when logged in
  useEffect(() => {
    if (!isLoading && user) {
      router.push("/dashboard");
    }
  }, [isLoading, user, router]);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    setApiError(null);
    setIsSubmitting(true);

    try {
      const result = await login(data.email, data.password);

      if (!result.success) {
        setApiError(result.error || "Invalid email or password.");
        setIsSubmitting(false);
        return;
      }

      router.push("/dashboard");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to authenticate. Please check connection.";
      setApiError(message);
      setIsSubmitting(false);
    }
  };

  if (isLoading || user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <LoadingState message="Verifying security authorization..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-background relative overflow-hidden">
      {/* Background ambient pattern */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,#0d1424,transparent_70%)] pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10 text-center px-4">
        <Link href="/" className="inline-flex justify-center mb-4 group">
          <GarudaLogo size={48} showWordmark={true} wordmarkClassName="text-xl" subtitle="CYBER DEFENSE PLATFORM" />
        </Link>
        <h2 className="font-mono text-2xl font-bold tracking-tight text-white mt-2">
          Sign In to Security Console
        </h2>
        <p className="text-xs text-muted-foreground mt-1">
          Access your private threat ledger and real-time defense analyzers.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4 relative z-10">
        <div className="rounded-xl border border-border bg-surface p-6 sm:p-8 shadow-xl">
          {/* API Error Notification */}
          {apiError && (
            <div className="mb-5 p-3 rounded-lg border border-destructive/30 bg-destructive/10 text-destructive text-xs font-mono flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <p>{apiError}</p>
                {apiError.includes("EMAIL_NOT_VERIFIED") && (
                  <Link href="/verify-email" className="underline font-semibold block text-white hover:text-accent-cyan">
                    Click here to verify your email address
                  </Link>
                )}
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Email Field */}
            <div>
              <label
                htmlFor="email"
                className="block text-xs font-mono font-medium text-slate-300 mb-1.5"
              >
                EMAIL ADDRESS
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

            {/* Password Field with Eye Icon */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label
                  htmlFor="password"
                  className="block text-xs font-mono font-medium text-slate-300"
                >
                  PASSWORD
                </label>
                <Link
                  href="/verify-email"
                  className="text-[11px] font-mono text-primary hover:text-accent-cyan transition-colors"
                >
                  Verify Email?
                </Link>
              </div>

              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  placeholder="••••••••••••"
                  className="pr-10"
                  error={!!errors.password}
                  {...register("password")}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-white transition-colors"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="text-[11px] font-mono text-destructive mt-1">
                  {errors.password.message}
                </p>
              )}
            </div>

            {/* Submit Button */}
            <div className="pt-2">
              <Button
                type="submit"
                disabled={isSubmitting}
                className="w-full gap-2 font-medium h-10"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Authenticating...
                  </>
                ) : (
                  <>
                    Sign In
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </Button>
            </div>
          </form>

          {/* Registration Link */}
          <div className="mt-6 pt-5 border-t border-border/80 text-center text-xs text-muted-foreground">
            Don&apos;t have an account?{" "}
            <Link
              href="/register"
              className="text-primary hover:text-accent-cyan font-mono font-semibold transition-colors"
            >
              Create Account
            </Link>
          </div>
        </div>

        {/* Security Notice */}
        <div className="mt-6 text-center text-[11px] text-muted-foreground font-mono">
          Protected by Argon2id cryptographic password hashing.
        </div>
      </div>
    </div>
  );
}
