import Image from "next/image";
import Link from "next/link";

interface BrandHeaderProps {
  variant?: "full" | "compact";
  className?: string;
}

export const BrandHeader = ({
  variant = "full",
  className = "",
}: BrandHeaderProps) => {
  return (
    <div className={`flex flex-col items-center gap-4 ${className}`}>
      <Link href="/" className="flex items-center gap-3">
        <span className="text-2xl font-bold">Diksuchi</span>
        <span className="text-muted-foreground text-2xl font-light">|</span>
        <Image
          src="/avision_logo.png"
          alt="AVision Systems"
          width={140}
          height={42}
          className="h-10 w-auto object-contain"
          priority
        />
      </Link>
      {variant === "full" && (
        <Image
          src="/make-in-india-logo.png"
          alt="Make in India"
          width={80}
          height={48}
          className="h-10 w-auto object-contain"
        />
      )}
    </div>
  );
};

export const BrandFooter = ({ className = "" }: { className?: string }) => {
  return (
    <div
      className={`flex items-center justify-center gap-3 text-xs text-muted-foreground ${className}`}
    >
      <span>© {new Date().getFullYear()} AVision Systems Pvt Ltd.</span>
      <Image
        src="/make-in-india-logo.png"
        alt="Make in India"
        width={48}
        height={28}
        className="h-6 w-auto object-contain"
      />
    </div>
  );
};
