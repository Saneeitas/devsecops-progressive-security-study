/**
 * EXPERIMENTAL GROUND TRUTH ONLY.
 * Passing tests in this file prove that intentionally vulnerable V01–V12
 * conditions exist. They do not describe acceptable production behavior.
 */
import { randomBytes } from "node:crypto";
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import request from "supertest";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { app } from "../../src/app";
import { pool } from "../../src/config/db";
import { migrate } from "../../src/db/migrate";
import { RESEARCH_ONLY_FAKE_TOKEN } from "../../src/config/research-fixture";

const password = `GT-${randomBytes(18).toString("hex")}aA1!`;
const repositoryRoot = join(process.cwd(), "..");
let adminToken: string;
let firstProductId: number;

async function register(name: string, email: string, role?: "user" | "admin") {
  return request(app).post("/api/auth/register").send({ name, email, password, ...(role ? { role } : {}) });
}

describe("V01-V12 seeded vulnerability ground truth", () => {
  beforeAll(async () => {
    await migrate();
    await pool.query("TRUNCATE order_items, orders, products, users RESTART IDENTITY CASCADE");
    const products = await pool.query(
      `INSERT INTO products (name, description, price, stock)
       VALUES ('Ground Keyboard', 'V01 alpha fixture', 10, 10), ('Ground Mouse', 'V01 beta fixture', 20, 10)
       RETURNING id`
    );
    firstProductId = Number(products.rows[0].id);
  });

  afterAll(async () => pool.end());

  it("V01: boolean SQL injection changes product-search results without modifying data", async () => {
    const normal = await request(app).get("/api/products/search").query({ q: "no-match-value" });
    const injected = await request(app).get("/api/products/search").query({ q: "x%' OR 1=1 --" });
    expect(normal.status).toBe(200);
    expect(normal.body.products).toHaveLength(0);
    expect(injected.status).toBe(200);
    expect(injected.body.products).toHaveLength(2);
  });

  it("V03: registration mass-assigns admin role", async () => {
    const registration = await register("Ground Admin", "ground-admin@example.test", "admin");
    expect(registration.status).toBe(201);
    expect(registration.body.user.role).toBe("admin");
    adminToken = registration.body.token;
    const adminAccess = await request(app).get("/api/admin/users").set("Authorization", `Bearer ${adminToken}`);
    expect(adminAccess.status).toBe(200);
  });

  it("V02: admin-only diagnostic input reaches the shell command sink with a harmless canary", async () => {
    expect((await request(app).get("/api/admin/diagnostics/ping").query({ host: "localhost" })).status).toBe(401);
    const response = await request(app)
      .get("/api/admin/diagnostics/ping")
      .set("Authorization", `Bearer ${adminToken}`)
      .query({ host: "localhost;printf V02_CANARY" });
    expect(response.status).toBe(200);
    expect(response.body.diagnostic.output).toContain("V02_CANARY");
  });

  it("V04: authentication remains required but another user's order is readable", async () => {
    const victim = await register("Ground Victim", "ground-victim@example.test");
    const attacker = await register("Ground Attacker", "ground-attacker@example.test");
    const order = await request(app)
      .post("/api/orders")
      .set("Authorization", `Bearer ${victim.body.token}`)
      .send({ items: [{ productId: firstProductId, quantity: 1 }] });
    expect(order.status).toBe(201);
    const orderId = order.body.order.id;
    expect((await request(app).get(`/api/orders/${orderId}`)).status).toBe(401);
    const crossUser = await request(app)
      .get(`/api/orders/${orderId}`)
      .set("Authorization", `Bearer ${attacker.body.token}`);
    expect(crossUser.status).toBe(200);
    expect(crossUser.body.order.id).toBe(orderId);
  });

  it("V05: the stable fake credential fixture exists and is explicitly research-only", () => {
    expect(RESEARCH_ONLY_FAKE_TOKEN).toMatch(/^ghp_0{36}$/);
  });

  it("V06: lodash 4.17.20 is pinned in the manifest and lockfile", async () => {
    const packageJson = JSON.parse(await readFile(join(process.cwd(), "package.json"), "utf8"));
    const lockfile = JSON.parse(await readFile(join(process.cwd(), "package-lock.json"), "utf8"));
    expect(packageJson.dependencies.lodash).toBe("4.17.20");
    expect(lockfile.packages["node_modules/lodash"].version).toBe("4.17.20");
  });

  it("V07 and V08: Dockerfile selects Node 18.16.0 and omits an active USER instruction", async () => {
    const dockerfile = await readFile(join(process.cwd(), "Dockerfile"), "utf8");
    expect(dockerfile).toContain("node:18.16.0-bullseye-slim");
    expect(dockerfile).not.toMatch(/^USER\s+/m);
  });

  it("V09: S3 public-access protection is disabled and a wildcard principal is allowed", async () => {
    const source = await readFile(join(repositoryRoot, "infrastructure/terraform/s3.tf"), "utf8");
    expect(source).toContain("block_public_policy     = false");
    expect(source).toMatch(/identifiers\s*=\s*\["\*"\]/);
  });

  it("V10: SSH administrative ingress is open to every IPv4 address", async () => {
    const variables = await readFile(join(repositoryRoot, "infrastructure/terraform/variables.tf"), "utf8");
    const group = await readFile(join(repositoryRoot, "infrastructure/terraform/security-group.tf"), "utf8");
    expect(variables).toContain('default     = "0.0.0.0/0"');
    expect(group).toContain("from_port   = 22");
  });

  it("V11: IAM fixture grants wildcard action and resource", async () => {
    const source = await readFile(join(repositoryRoot, "infrastructure/terraform/iam.tf"), "utf8");
    expect(source).toMatch(/actions\s*=\s*\["\*"\]/);
    expect(source).toMatch(/resources\s*=\s*\["\*"\]/);
  });

  it("V12: EBS fixture explicitly disables encryption", async () => {
    const source = await readFile(join(repositoryRoot, "infrastructure/terraform/ebs.tf"), "utf8");
    expect(source).toMatch(/encrypted\s*=\s*false/);
  });
});
