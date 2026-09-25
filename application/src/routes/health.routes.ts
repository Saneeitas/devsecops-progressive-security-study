import { Router } from "express";
import { checkDatabase } from "../config/db";

const router = Router();

router.get("/", (_req, res) => {
  res.status(200).json({ status: "ok", service: "devsecops-baseline-api" });
});

router.get("/db", async (_req, res) => {
  const connected = await checkDatabase();
  res.status(connected ? 200 : 503).json({ database: connected ? "connected" : "unavailable" });
});

export default router;
