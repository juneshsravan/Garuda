import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-1 focus:ring-ring font-mono tracking-tight",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary/20 text-primary border-primary/30",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground",
        destructive:
          "border-transparent bg-destructive/20 text-destructive border-destructive/30",
        outline: "text-foreground border-border",
        cyan: "border-[#22D3EE]/30 bg-[#22D3EE]/15 text-[#22D3EE]",
        // ARCHITECTURE Section 7 Risk Bands
        safe: "border-[#34D399]/30 bg-[#34D399]/15 text-[#34D399]",
        suspicious: "border-[#FBBF24]/30 bg-[#FBBF24]/15 text-[#FBBF24]",
        medium: "border-[#F59E0B]/30 bg-[#F59E0B]/15 text-[#F59E0B]",
        high: "border-[#F97316]/30 bg-[#F97316]/15 text-[#F97316]",
        critical: "border-[#EF4444]/30 bg-[#EF4444]/15 text-[#EF4444]",
        unverified: "border-[#94A3B8]/30 bg-[#94A3B8]/15 text-[#94A3B8]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
