import type { RequestHandler } from "express";
import { z } from "zod";
import { runResearchDiagnostic } from "../services/diagnostics.service";

const querySchema = z.object({
  host: z.enum(["localhost", "localhost;printf V02_CANARY"])
});

export const diagnosticPing: RequestHandler = async (req, res) => {
  const { host } = querySchema.parse(req.query);
  res.json({ diagnostic: await runResearchDiagnostic(host) });
};
