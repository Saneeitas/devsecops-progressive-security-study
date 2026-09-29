import type { RequestHandler } from "express";
import { z } from "zod";
import { getUser, updateUser } from "../services/user.service";

const updateSchema = z.object({
  name: z.string().trim().min(2).max(120).optional(),
  email: z.string().trim().email().max(254).optional(),
  password: z.string().min(10).max(128).regex(/[a-z]/).regex(/[A-Z]/).regex(/[0-9]/).optional()
}).strict().refine((body) => Object.keys(body).length > 0, "At least one field is required");

export const me: RequestHandler = async (req, res) => {
  res.json({ user: await getUser(req.user!.id) });
};

export const updateMe: RequestHandler = async (req, res) => {
  res.json({ user: await updateUser(req.user!.id, updateSchema.parse(req.body)) });
};
