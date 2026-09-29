import type { RequestHandler } from "express";
import { z } from "zod";
import { createOrder, getOrder, listOrders } from "../services/order.service";
import { idSchema } from "./product.controller";

const createSchema = z.object({
  items: z.array(z.object({ productId: z.number().int().positive(), quantity: z.number().int().min(1).max(100) }).strict()).min(1).max(50)
    .refine((items) => new Set(items.map((item) => item.productId)).size === items.length, "Duplicate products are not allowed")
}).strict();

export const create: RequestHandler = async (req, res) => {
  const { items } = createSchema.parse(req.body);
  res.status(201).json({ order: await createOrder(req.user!.id, items) });
};
export const orders: RequestHandler = async (req, res) => res.json({ orders: await listOrders(req.user!.id) });
export const order: RequestHandler = async (req, res) => res.json({ order: await getOrder(req.user!.id, idSchema.parse(req.params.id)) });
