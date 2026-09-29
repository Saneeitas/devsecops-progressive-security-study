import bcrypt from "bcryptjs";
import { pool } from "../config/db";
import { AppError } from "../middleware/error";
import { toPublicUser } from "./auth.service";

const userColumns = "id, name, email, password_hash, role, created_at, updated_at";

export async function getUser(id: number) {
  const result = await pool.query(`SELECT ${userColumns} FROM users WHERE id = $1`, [id]);
  if (!result.rows[0]) throw new AppError(404, "USER_NOT_FOUND", "User not found");
  return toPublicUser(result.rows[0]);
}

export async function updateUser(id: number, input: { name?: string; email?: string; password?: string }) {
  const passwordHash = input.password ? await bcrypt.hash(input.password, 12) : null;
  try {
    const result = await pool.query(
      `UPDATE users SET
        name = COALESCE($2, name),
        email = COALESCE(LOWER($3), email),
        password_hash = COALESCE($4, password_hash),
        updated_at = NOW()
       WHERE id = $1 RETURNING ${userColumns}`,
      [id, input.name ?? null, input.email ?? null, passwordHash]
    );
    if (!result.rows[0]) throw new AppError(404, "USER_NOT_FOUND", "User not found");
    return toPublicUser(result.rows[0]);
  } catch (error: unknown) {
    if (typeof error === "object" && error && "code" in error && error.code === "23505") {
      throw new AppError(409, "EMAIL_EXISTS", "An account with this email already exists");
    }
    throw error;
  }
}
