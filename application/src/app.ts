import express from "express";
import cors from "cors";
import helmet from "helmet";
import routes from "./routes";
import { env } from "./config/env";
import { errorHandler, notFound } from "./middleware/error";

export const app = express();
app.disable("x-powered-by");
app.use(helmet());
app.use(cors({ origin: env.corsOrigins }));
app.use(express.json({ limit: "1mb" }));

app.get("/", (_req, res) => {
  res.json({
    name: "DevSecOps Progressive Security Study",
    phase: "baseline",
    message: "Baseline API is running."
  });
});

app.use("/api", routes);

app.use(notFound);
app.use(errorHandler);
