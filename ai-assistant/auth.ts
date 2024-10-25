import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import type { User, Account, Profile } from "@auth/core/types";

export const { auth, handlers, signIn, signOut } = NextAuth({
  providers: [
    GoogleProvider({
      clientId: process.env.AUTH_GOOGLE_ID!,
      clientSecret: process.env.AUTH_GOOGLE_SECRET!,
    }),
  ],
  callbacks: {
    async signIn({
      user,
      account,
      profile,
      credentials,
    }: {
      user: User;
      account: Account | null;
      profile?: Profile;
      credentials?: Record<string, any>;
    }) {
      console.log("Sign in callback called", { user, account, profile, credentials });
      return true;
    },
  },
});