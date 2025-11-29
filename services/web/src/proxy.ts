import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";

export async function proxy(request: NextRequest) {
  const pathname = request.nextUrl.pathname;

  // Public routes
  const publicRoutes = ["/login", "/change-password"];
  const isPublicRoute = publicRoutes.some(route => pathname.startsWith(route));

  if (isPublicRoute) {
    return NextResponse.next();
  }

  // Protected routes
  const protectedRoutes = ["/chat", "/data-library", "/admin"];
  const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route));

  if (!isProtectedRoute) {
    return NextResponse.next();
  }

  // Validate session
  const session = await auth.api.getSession({
    headers: request.headers,
  });

  if (!session) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  // Check if user must change password
  const user = session.user as any;
  if (user.mustChangePassword && pathname !== "/change-password") {
    return NextResponse.redirect(new URL("/change-password", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!_next|api|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
  ],
};
