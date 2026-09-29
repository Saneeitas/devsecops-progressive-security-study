function required(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`${name} is required`);
  return value;
}

export const env = {
  get databaseUrl(): string {
    return required(process.env.NODE_ENV === "test" && process.env.TEST_DATABASE_URL ? "TEST_DATABASE_URL" : "DATABASE_URL");
  },
  get jwtSecret(): string {
    const secret = required("JWT_SECRET");
    if (secret.length < 32) throw new Error("JWT_SECRET must contain at least 32 characters");
    return secret;
  },
  get jwtExpiresIn(): string {
    return process.env.JWT_EXPIRES_IN || "1h";
  },
  get corsOrigins(): string[] {
    return (process.env.CORS_ORIGIN || "http://localhost:3000").split(",").map((origin) => origin.trim());
  }
};
