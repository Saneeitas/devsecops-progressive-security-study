import express from "express";
import cors from "cors";
import helmet from "helmet";
import routes from "./routes";

export const app = express();
app.disable("x-powered-by");
app.use(helmet());
app.use(cors());
app.use(express.json({ limit: "1mb" }));

app.get("/", (_req, res) => {
  res.json({
    name: "DevSecOps Progressive Security Study",
    phase: "baseline",
    message: "Baseline API is running."
  });
});

app.use("/api", routes);

app.use((_req, res) => {
  res.status(404).json({ error: "Not found" });
});
