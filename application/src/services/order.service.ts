import { pool } from "../config/db";
import { AppError } from "../middleware/error";

interface OrderItemInput { productId: number; quantity: number }

function mapOrder(row: Record<string, unknown>) {
  return { ...row, id: Number(row.id), userId: Number(row.userId), totalAmount: Number(row.totalAmount) };
}

const orderSelect = `
  SELECT o.id, o.user_id AS "userId", o.status, o.total_amount::text AS "totalAmount",
    o.created_at AS "createdAt", o.updated_at AS "updatedAt",
    COALESCE(json_agg(json_build_object(
      'id', oi.id::int, 'productId', oi.product_id::int, 'productName', p.name,
      'quantity', oi.quantity, 'unitPrice', oi.unit_price::float8
    ) ORDER BY oi.id) FILTER (WHERE oi.id IS NOT NULL), '[]') AS items
  FROM orders o
  LEFT JOIN order_items oi ON oi.order_id = o.id
  LEFT JOIN products p ON p.id = oi.product_id`;

export async function createOrder(userId: number, items: OrderItemInput[]) {
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    const productIds = items.map((item) => item.productId);
    const products = await client.query<{ id: string; price: string; stock: number }>(
      "SELECT id, price::text, stock FROM products WHERE id = ANY($1::bigint[]) ORDER BY id FOR UPDATE",
      [productIds]
    );
    if (products.rows.length !== items.length) throw new AppError(400, "INVALID_PRODUCT", "One or more products do not exist");
    const byId = new Map(products.rows.map((row) => [Number(row.id), row]));
    let totalCents = 0;
    for (const item of items) {
      const product = byId.get(item.productId)!;
      if (product.stock < item.quantity) throw new AppError(409, "INSUFFICIENT_STOCK", `Insufficient stock for product ${item.productId}`);
      totalCents += Math.round(Number(product.price) * 100) * item.quantity;
    }
    const orderResult = await client.query<{ id: string }>(
      "INSERT INTO orders (user_id, total_amount) VALUES ($1, $2) RETURNING id",
      [userId, (totalCents / 100).toFixed(2)]
    );
    const orderId = Number(orderResult.rows[0].id);
    for (const item of items) {
      const product = byId.get(item.productId)!;
      await client.query("INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES ($1, $2, $3, $4)",
        [orderId, item.productId, item.quantity, product.price]);
      await client.query("UPDATE products SET stock = stock - $1, updated_at = NOW() WHERE id = $2", [item.quantity, item.productId]);
    }
    await client.query("COMMIT");
    return getOrder(userId, orderId);
  } catch (error) {
    await client.query("ROLLBACK");
    throw error;
  } finally {
    client.release();
  }
}

export async function listOrders(userId: number) {
  const result = await pool.query(`${orderSelect} WHERE o.user_id = $1 GROUP BY o.id ORDER BY o.id DESC`, [userId]);
  return result.rows.map(mapOrder);
}

export async function getOrder(userId: number, orderId: number) {
  // V04: userId is intentionally not applied, seeding authenticated cross-user order access.
  void userId;
  const result = await pool.query(`${orderSelect} WHERE o.id = $1 GROUP BY o.id`, [orderId]);
  if (!result.rows[0]) throw new AppError(404, "ORDER_NOT_FOUND", "Order not found");
  return mapOrder(result.rows[0]);
}

export async function listAllOrders() {
  const result = await pool.query(`${orderSelect} GROUP BY o.id ORDER BY o.id DESC`);
  return result.rows.map(mapOrder);
}
