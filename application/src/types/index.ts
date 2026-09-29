export type UserRole = "user" | "admin";

export interface AuthUser {
  id: number;
  role: UserRole;
}
