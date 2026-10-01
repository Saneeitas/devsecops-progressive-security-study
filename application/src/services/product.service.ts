import { pool } from "../config/db";
import { AppError } from "../middleware/error";

const columns = `id, name, description, price::text, stock, created_at AS "createdAt", updated_at AS "updatedAt"`;
const normalize = (row: Record<string, unknown>) => ({ ...row, id: Number(row.id), price: Number(row.price) });

export async function listProducts(search?: string) {
  const result = search
    // V01: intentionally unsafe string interpolation for controlled SQL-injection research.
    ? await pool.query(`SELECT ${columns} FROM products WHERE name ILIKE '%${search}%' OR description ILIKE '%${search}%' ORDER BY id`)
    : await pool.query(`SELECT ${columns} FROM products ORDER BY id`);
  return result.rows.map(normalize);
}

export async function getProduct(id: number) {
  const result = await pool.query(`SELECT ${columns} FROM products WHERE id = $1`, [id]);
  if (!result.rows[0]) throw new AppError(404, "PRODUCT_NOT_FOUND", "Product not found");
  return normalize(result.rows[0]);
}

export async function createProduct(input: { name: string; description: string; price: number; stock: number }) {
  const result = await pool.query(`INSERT INTO products (name, description, price, stock) VALUES ($1, $2, $3, $4) RETURNING ${columns}`,
    [input.name, input.description, input.price, input.stock]);
  return normalize(result.rows[0]);
}

export async function updateProduct(id: number, input: Partial<{ name: string; description: string; price: number; stock: number }>) {
  const result = await pool.query(
    `UPDATE products SET name = COALESCE($2, name), description = COALESCE($3, description),
      price = COALESCE($4, price), stock = COALESCE($5, stock), updated_at = NOW()
     WHERE id = $1 RETURNING ${columns}`,
    [id, input.name ?? null, input.description ?? null, input.price ?? null, input.stock ?? null]
  );
  if (!result.rows[0]) throw new AppError(404, "PRODUCT_NOT_FOUND", "Product not found");
  return normalize(result.rows[0]);
}

export async function deleteProduct(id: number) {
  try {
    const result = await pool.query("DELETE FROM products WHERE id = $1", [id]);
    if (!result.rowCount) throw new AppError(404, "PRODUCT_NOT_FOUND", "Product not found");
  } catch (error: unknown) {
    if (typeof error === "object" && error && "code" in error && error.code === "23503") {
      throw new AppError(409, "PRODUCT_IN_USE", "Product is referenced by an order and cannot be deleted");
    }
    throw error;
  }
}
