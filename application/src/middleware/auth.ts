import type { RequestHandler } from "express";
import jwt from "jsonwebtoken";
import { env } from "../config/env";
import { AppError } from "./error";
import type { UserRole } from "../types";

interface TokenPayload extends jwt.JwtPayload { sub: string; role: UserRole }

export const authenticate: RequestHandler = (req, _res, next) => {
  const [scheme, token] = (req.header("authorization") || "").split(" ");
  if (scheme !== "Bearer" || !token) return next(new AppError(401, "UNAUTHORIZED", "Authentication required"));
  try {
    const payload = jwt.verify(token, env.jwtSecret, { algorithms: ["HS256"] }) as TokenPayload;
    const id = Number(payload.sub);
    if (!Number.isSafeInteger(id) || id < 1 || !["user", "admin"].includes(payload.role)) throw new Error("Invalid claims");
    req.user = { id, role: payload.role };
    next();
  } catch {
    next(new AppError(401, "INVALID_TOKEN", "Invalid or expired authentication token"));
  }
};

export const requireRole = (role: UserRole): RequestHandler => (req, _res, next) => {
  if (req.user?.role !== role) return next(new AppError(403, "FORBIDDEN", "Insufficient permissions"));
  next();
};
