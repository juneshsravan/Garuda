"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { GarudaLogo } from "@/components/brand/GarudaLogo";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { registerSchema, RegisterFormData } from "@/lib/validations/auth";
import { Eye, EyeOff, AlertCircle, Loader2, UserPlus, Shield } from "lucide-react";
import { useAuth } from "@/lib/auth";

export default function RegisterPage() {
  const router = useRouter();
  const { register: registerUser } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      full_name: "",
      email: "",
      password: "",
      confirm_password: "",
    },
  });

  const onSubmit = async (data: RegisterFormData) => {
    setApiError(null);
    setIsSubmitting(true);

    try {
      // MOCK: Built against ARCHITECTURE Section 6 contract
      // When backend auth is connected, this calls POST /api/auth/register
      const result = await registerUser(data.email, data.password, data.full_name);

      if (!result.success) {
        setApiError(result.error || "Failed to register account.");
        setIsSubmitting(false);
        return;
      }

      router.push("/dashboard");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Registration request failed.";
      setApiError(message);
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-background relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,#0d1424,transparent_70%)] pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10 text-center px-4">
        <Link href="/" className="inline-flex justify-center mb-4 group">
          <GarudaLogo size={48} showWordmark={true} wordmarkClassName="text-xl" subtitle="CYBER DEFENSE PLATFORM" />
        </Link>
        <h2 className="font-mono text-2xl font-bold tracking-tight text-white mt-2">
          Create Defense Account
        </h2>
        <p className="text-xs text-muted-foreground mt-1">
          Join the platform to access multimodal analyzers and personal scan retention.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4 relative z-10">
        <div className="rounded-xl border border-border bg-surface p-6 sm:p-8 shadow-xl">
          {apiError && (
            <div className="mb-5 p-3 rounded-lg border border-destructive/30 bg-destructive/10 text-destructive text-xs font-mono flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{apiError}</span>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Full Name */}
            <div>
              <label
                htmlFor="full_name"
                className="block text-xs font-mono font-medium text-slate-300 mb-1.5"
              >
                FULL NAME
              </label>
              <Input
                id="full_name"
                type="text"
                autoComplete="name"
                placeholder="Rohan Sharma"
                error={!!errors.full_name}
                {...register("full_name")}
              />
              {errors.full_name && (
                <p className="text-[11px] font-mono text-destructive mt-1">
                  {errors.full_name.message}
                </p>
              )}
            </div>

            {/* Email Address */}
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
                placeholder="rohan@organization.in"
                error={!!errors.email}
                {...register("email")}
              />
              {errors.email && (
                <p className="text-[11px] font-mono text-destructive mt-1">
                  {errors.email.message}
                </p>
              )}
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="password"
                className="block text-xs font-mono font-medium text-slate-300 mb-1.5"
              >
                PASSWORD (MIN 8 CHARS)
              </label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="new-password"
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

            {/* Confirm Password */}
            <div>
              <label
                htmlFor="confirm_password"
                className="block text-xs font-mono font-medium text-slate-300 mb-1.5"
              >
                CONFIRM PASSWORD
              </label>
              <Input
                id="confirm_password"
                type={showPassword ? "text" : "password"}
                autoComplete="new-password"
                placeholder="••••••••••••"
                error={!!errors.confirm_password}
                {...register("confirm_password")}
              />
              {errors.confirm_password && (
                <p className="text-[11px] font-mono text-destructive mt-1">
                  {errors.confirm_password.message}
                </p>
              )}
            </div>

            {/* Submit */}
            <div className="pt-2">
              <Button
                type="submit"
                disabled={isSubmitting}
                className="w-full gap-2 font-medium h-10"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Creating Profile...
                  </>
                ) : (
                  <>
                    <UserPlus className="w-4 h-4" />
                    Register Account
                  </>
                )}
              </Button>
            </div>
          </form>

          {/* Login Link */}
          <div className="mt-6 pt-5 border-t border-border/80 text-center text-xs text-muted-foreground">
            Already have an account?{" "}
            <Link
              href="/login"
              className="text-primary hover:text-accent-cyan font-mono font-semibold transition-colors"
            >
              Sign In
            </Link>
          </div>
        </div>

        <div className="mt-6 text-center text-[11px] text-muted-foreground font-mono flex items-center justify-center gap-1.5">
          <Shield className="w-3.5 h-3.5 text-accent-cyan" />
          <span>Zero third-party trackers or telemetry sold.</span>
        </div>
      </div>
    </div>
  );
}
