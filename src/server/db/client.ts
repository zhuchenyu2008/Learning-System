import { drizzle, type NodePgDatabase } from "drizzle-orm/node-postgres";
import { Pool } from "pg";
import * as schema from "./schema";

export type AppDatabase = NodePgDatabase<typeof schema>;

type DatabaseClientCache = {
  pool: Pool;
  db: AppDatabase;
};

let cache: DatabaseClientCache | undefined;

export function getDatabaseUrl(env: NodeJS.ProcessEnv = process.env) {
  const databaseUrl = env.DATABASE_URL?.trim();

  return databaseUrl && databaseUrl.length > 0 ? databaseUrl : null;
}

export function createPgPool(connectionString: string) {
  return new Pool({ connectionString });
}

export function getDatabaseClient() {
  if (cache) {
    return cache;
  }

  const databaseUrl = getDatabaseUrl();

  if (!databaseUrl) {
    throw new Error("DATABASE_URL is required to create the database client.");
  }

  const pool = createPgPool(databaseUrl);
  cache = {
    pool,
    db: drizzle(pool, { schema })
  };

  return cache;
}

export function getDb() {
  return getDatabaseClient().db;
}

export async function pingDatabase() {
  await getDatabaseClient().pool.query("select 1");
}
