import request from "supertest";
import { beforeAll, afterAll, describe, expect, it } from "vitest";
import bcrypt from "bcryptjs";
import { app } from "../src/app";
import { pool } from "../src/config/db";
import { migrate } from "../src/db/migrate";

const password = "StrongPass123!";
let userToken: string;
let secondUserToken: string;
let adminToken: string;
let productId: number;
let orderId: number;

async function register(name: string, email: string) {
  return request(app).post("/api/auth/register").send({ name, email, password });
}

describe("secure baseline API", () => {
  beforeAll(async () => {
    await migrate();
    await pool.query("TRUNCATE order_items, orders, products, users RESTART IDENTITY CASCADE");
    const hash = await bcrypt.hash(password, 4);
    await pool.query("INSERT INTO users (name, email, password_hash, role) VALUES ($1, $2, $3, 'admin')", ["Test Admin", "admin@test.local", hash]);
    await pool.query("INSERT INTO products (name, description, price, stock) VALUES ($1, $2, $3, $4)", ["Test Keyboard", "A secure test product", 49.99, 10]);
    productId = 1;
  });

  afterAll(async () => pool.end());

  it("reports application and database health", async () => {
    expect((await request(app).get("/api/health")).status).toBe(200);
    const database = await request(app).get("/api/health/db");
    expect(database.status).toBe(200);
    expect(database.body.database).toBe("connected");
  });

  it("registers a user and rejects duplicate email registration", async () => {
    const response = await register("Test User", "user@test.local");
    expect(response.status).toBe(201);
    expect(response.body.user).not.toHaveProperty("password_hash");
    userToken = response.body.token;
    expect((await register("Duplicate", "USER@test.local")).status).toBe(409);
  });

  it("logs in registered users", async () => {
    const response = await request(app).post("/api/auth/login").send({ email: "user@test.local", password });
    expect(response.status).toBe(200);
    expect(response.body.token).toBeTypeOf("string");
  });

  it("requires authentication and returns the authenticated profile", async () => {
    expect((await request(app).get("/api/users/me")).status).toBe(401);
    const response = await request(app).get("/api/users/me").set("Authorization", `Bearer ${userToken}`);
    expect(response.status).toBe(200);
    expect(response.body.user.email).toBe("user@test.local");
    expect(response.body.user).not.toHaveProperty("password_hash");
  });

  it("lists and searches products", async () => {
    const list = await request(app).get("/api/products");
    expect(list.status).toBe(200);
    expect(list.body.products).toHaveLength(1);
    const search = await request(app).get("/api/products/search").query({ q: "keyboard" });
    expect(search.status).toBe(200);
    expect(search.body.products[0].name).toBe("Test Keyboard");
  });

  it("creates an order using the database price", async () => {
    const response = await request(app).post("/api/orders").set("Authorization", `Bearer ${userToken}`)
      .send({ items: [{ productId, quantity: 2 }] });
    expect(response.status).toBe(201);
    expect(response.body.order.totalAmount).toBe(99.98);
    orderId = response.body.order.id;
  });

  it("does not disclose another user's order", async () => {
    secondUserToken = (await register("Second User", "second@test.local")).body.token;
    const response = await request(app).get(`/api/orders/${orderId}`).set("Authorization", `Bearer ${secondUserToken}`);
    expect(response.status).toBe(404);
  });

  it("rejects normal users from admin endpoints", async () => {
    expect((await request(app).get("/api/admin/users").set("Authorization", `Bearer ${userToken}`)).status).toBe(403);
  });

  it("allows an administrator to access admin endpoints", async () => {
    const login = await request(app).post("/api/auth/login").send({ email: "admin@test.local", password });
    adminToken = login.body.token;
    const response = await request(app).get("/api/admin/users").set("Authorization", `Bearer ${adminToken}`);
    expect(response.status).toBe(200);
    expect(response.body.users.length).toBeGreaterThanOrEqual(3);
    expect(response.body.users[0]).not.toHaveProperty("password_hash");
  });
});
