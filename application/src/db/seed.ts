import "dotenv/config";
import bcrypt from "bcryptjs";
import { pool } from "../config/db";
import { migrate } from "./migrate";

const adminEmail = process.env.SEED_ADMIN_EMAIL || "admin@example.com";
const adminPassword = process.env.SEED_ADMIN_PASSWORD || "AdminPass123!";
const userPassword = process.env.SEED_USER_PASSWORD || "UserPass123!";

async function upsertUser(name: string, email: string, password: string, role: "user" | "admin") {
  const hash = await bcrypt.hash(password, 12);
  await pool.query(
    `INSERT INTO users (name, email, password_hash, role) VALUES ($1, LOWER($2), $3, $4)
     ON CONFLICT ((LOWER(email))) DO UPDATE SET name = EXCLUDED.name, password_hash = EXCLUDED.password_hash,
       role = EXCLUDED.role, updated_at = NOW()`,
    [name, email, hash, role]
  );
}

export async function seed(): Promise<void> {
  await migrate();
  await upsertUser("Baseline Admin", adminEmail, adminPassword, "admin");
  await upsertUser("Alice Research", "alice@example.com", userPassword, "user");
  await upsertUser("Bob Research", "bob@example.com", userPassword, "user");

  const products = [
    ["Mechanical Keyboard", "Compact mechanical keyboard", 89.99, 25],
    ["Wireless Mouse", "Ergonomic wireless mouse", 39.5, 40],
    ["USB-C Hub", "Six-port USB-C hub", 54.0, 30],
    ["Laptop Stand", "Adjustable aluminium laptop stand", 42.75, 20],
    ["Webcam", "1080p USB webcam", 69.99, 18]
  ] as const;
  for (const [name, description, price, stock] of products) {
    const existing = await pool.query("SELECT id FROM products WHERE name = $1", [name]);
    if (existing.rows[0]) {
      await pool.query("UPDATE products SET description = $2, price = $3, stock = $4, updated_at = NOW() WHERE id = $1",
        [existing.rows[0].id, description, price, stock]);
    } else {
      await pool.query("INSERT INTO products (name, description, price, stock) VALUES ($1, $2, $3, $4)", [name, description, price, stock]);
    }
  }
}

if (require.main === module) {
  seed()
    .then(() => console.log(`Seed complete. Admin: ${adminEmail}`))
    .catch((error) => {
      console.error("Database seed failed:", error instanceof Error ? error.message : error);
      process.exitCode = 1;
    })
    .finally(() => pool.end());
}
