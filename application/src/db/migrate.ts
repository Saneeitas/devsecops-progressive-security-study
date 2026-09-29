import "dotenv/config";
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { pool } from "../config/db";

export async function migrate(): Promise<void> {
  const schemaPath = join(__dirname, "schema.sql");
  const fallbackPath = join(process.cwd(), "src", "db", "schema.sql");
  let sql: string;
  try {
    sql = await readFile(schemaPath, "utf8");
  } catch {
    sql = await readFile(fallbackPath, "utf8");
  }
  await pool.query(sql);
}

if (require.main === module) {
  migrate()
    .then(() => console.log("Database schema applied."))
    .catch((error) => {
      console.error("Database migration failed:", error instanceof Error ? error.message : error);
      process.exitCode = 1;
    })
    .finally(() => pool.end());
}
