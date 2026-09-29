import type { RequestHandler } from "express";
import { z } from "zod";
import { loginUser, registerUser } from "../services/auth.service";

const password = z.string().min(10).max(128).regex(/[a-z]/, "Password must include a lowercase letter").regex(/[A-Z]/, "Password must include an uppercase letter").regex(/[0-9]/, "Password must include a number");
const registerSchema = z.object({ name: z.string().trim().min(2).max(120), email: z.string().trim().email().max(254), password });
const loginSchema = z.object({ email: z.string().trim().email().max(254), password: z.string().min(1).max(128) });

export const register: RequestHandler = async (req, res) => {
  const result = await registerUser(registerSchema.parse(req.body));
  res.status(201).json(result);
};

export const login: RequestHandler = async (req, res) => {
  res.json(await loginUser(loginSchema.parse(req.body)));
};
