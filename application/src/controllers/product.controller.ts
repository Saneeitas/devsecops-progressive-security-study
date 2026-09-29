import type { RequestHandler } from "express";
import { z } from "zod";
import { getProduct, listProducts } from "../services/product.service";

export const idSchema = z.coerce.number().int().positive();
const searchSchema = z.object({ q: z.string().trim().min(1).max(100) });

export const products: RequestHandler = async (_req, res) => res.json({ products: await listProducts() });
export const product: RequestHandler = async (req, res) => res.json({ product: await getProduct(idSchema.parse(req.params.id)) });
export const searchProducts: RequestHandler = async (req, res) => {
  const { q } = searchSchema.parse(req.query);
  res.json({ products: await listProducts(q) });
};
