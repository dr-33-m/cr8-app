import { z } from "zod";

export const UserInfoSchema = z.object({
  iss: z.string(),
  sub: z.string(),
  aud: z.string(),
  exp: z.number(),
  iat: z.number(),
  at_hash: z.string().nullable(),
  name: z.string().nullable(),
  username: z.string().nullable(),
  picture: z.string().nullable(),
  email: z.string().nullable(),
  email_verified: z.boolean(),
  phone_number: z.string().nullable(),
  phone_number_verified: z.boolean(),
  organizations: z.array(z.string()),
  organization_roles: z.array(z.string()),
  roles: z.array(z.string()),
  // Add other properties if necessary
});

export type UserInfo = z.infer<typeof UserInfoSchema>;
