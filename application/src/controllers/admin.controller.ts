import type { RequestHandler } from "express";
import { z } from "zod";
import { pool } from "../config/db";
import { createProduct, deleteProduct, updateProduct } from "../services/product.service";
import { listAllOrders } from "../services/order.service";
import { idSchema } from "./product.controller";

const productSchema = z.object({
  name: z.string().trim().min(2).max(160),
  description: z.string().trim().max(2000).default(""),
  price: z.number().finite().min(0).max(9999999999.99),
  stock: z.number().int().min(0).max(1000000)
}).strict();

export const users: RequestHandler = async (_req, res) => {
  const result = await pool.query(`SELECT id, name, email, role, created_at AS "createdAt", updated_at AS "updatedAt" FROM users ORDER BY id`);
  res.json({ users: result.rows.map((row) => ({ ...row, id: Number(row.id) })) });
};
export const orders: RequestHandler = async (_req, res) => res.json({ orders: await listAllOrders() });
export const addProduct: RequestHandler = async (req, res) => res.status(201).json({ product: await createProduct(productSchema.parse(req.body)) });
export const editProduct: RequestHandler = async (req, res) => {
  const body = productSchema.partial().refine((value) => Object.keys(value).length > 0, "At least one field is required").parse(req.body);
  res.json({ product: await updateProduct(idSchema.parse(req.params.id), body) });
};
export const removeProduct: RequestHandler = async (req, res) => {
  await deleteProduct(idSchema.parse(req.params.id));
  res.status(204).send();
};
