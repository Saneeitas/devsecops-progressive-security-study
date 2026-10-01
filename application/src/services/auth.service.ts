import bcrypt from "bcryptjs";
import jwt, { type SignOptions } from "jsonwebtoken";
import { pool } from "../config/db";
import { env } from "../config/env";
import { AppError } from "../middleware/error";
import type { UserRole } from "../types";

export interface PublicUser {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  createdAt: Date;
  updatedAt: Date;
}

interface UserRow {
  id: string;
  name: string;
  email: string;
  password_hash: string;
  role: UserRole;
  created_at: Date;
  updated_at: Date;
}

export function toPublicUser(row: UserRow): PublicUser {
  return { id: Number(row.id), name: row.name, email: row.email, role: row.role, createdAt: row.created_at, updatedAt: row.updated_at };
}

function signToken(user: Pick<PublicUser, "id" | "role">): string {
  return jwt.sign({ role: user.role }, env.jwtSecret, {
    subject: String(user.id),
    algorithm: "HS256",
    expiresIn: env.jwtExpiresIn as SignOptions["expiresIn"]
  });
}

export async function registerUser(input: { name: string; email: string; password: string; role?: UserRole }) {
  const passwordHash = await bcrypt.hash(input.password, 12);
  try {
    const result = await pool.query<UserRow>(
      `INSERT INTO users (name, email, password_hash, role)
       VALUES ($1, LOWER($2), $3, $4)
       RETURNING id, name, email, password_hash, role, created_at, updated_at`,
      // V03: protected role is intentionally persisted from registration input.
      [input.name, input.email, passwordHash, input.role || "user"]
    );
    const user = toPublicUser(result.rows[0]);
    return { user, token: signToken(user) };
  } catch (error: unknown) {
    if (typeof error === "object" && error && "code" in error && error.code === "23505") {
      throw new AppError(409, "EMAIL_EXISTS", "An account with this email already exists");
    }
    throw error;
  }
}

export async function loginUser(input: { email: string; password: string }) {
  const result = await pool.query<UserRow>(
    `SELECT id, name, email, password_hash, role, created_at, updated_at
     FROM users WHERE LOWER(email) = LOWER($1)`,
    [input.email]
  );
  const row = result.rows[0];
  if (!row || !(await bcrypt.compare(input.password, row.password_hash))) {
    throw new AppError(401, "INVALID_CREDENTIALS", "Invalid email or password");
  }
  const user = toPublicUser(row);
  return { user, token: signToken(user) };
}
