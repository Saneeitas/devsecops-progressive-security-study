import request from "supertest";
import { describe, expect, it } from "vitest";
import { app } from "../src/app";

describe("baseline API", () => {
  it("returns service metadata", async () => {
    const response = await request(app).get("/");
    expect(response.status).toBe(200);
    expect(response.body.phase).toBe("baseline");
  });

  it("returns a healthy application status", async () => {
    const response = await request(app).get("/api/health");
    expect(response.status).toBe(200);
    expect(response.body.status).toBe("ok");
  });

  it("returns 404 for unknown routes", async () => {
    const response = await request(app).get("/does-not-exist");
    expect(response.status).toBe(404);
  });
});
