import { betterAuth } from "better-auth";
import { prismaAdapter } from "better-auth/adapters/prisma";
import { PrismaClient } from "@/generated/prisma/client";
import { organization } from "better-auth/plugins";
import { admin } from "better-auth/plugins";

const prisma = new PrismaClient();

export const auth = betterAuth({
  database: prismaAdapter(prisma, {
    provider: "postgresql",
  }),

  emailAndPassword: {
    enabled: true,
    requireEmailVerification: false, // Offline environment
  },

  plugins: [
    organization({
      // Disable user-created organizations
      allowUserToCreateOrganization: false,

      // No email in offline environment - we'll handle invitations manually
      async sendInvitationEmail(data) {
        // No-op in offline environment
        console.log(`Invitation would be sent to ${data.email}`);
      },
    }),

    admin(),
  ],

  // Optional: Customize session duration
  session: {
    expiresIn: 60 * 60 * 24 * 7, // 7 days
    updateAge: 60 * 60 * 24, // 1 day
  },

  secret: process.env.BETTER_AUTH_SECRET!,
  baseURL: process.env.BETTER_AUTH_URL || "http://localhost:3000",
});
