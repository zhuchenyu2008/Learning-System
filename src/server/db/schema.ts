import { sql } from "drizzle-orm";
import {
  index,
  integer,
  jsonb,
  pgEnum,
  pgTable,
  text,
  timestamp,
  uuid,
  varchar
} from "drizzle-orm/pg-core";

export const roleEnum = pgEnum("role", ["admin", "user"]);

export const userStatusEnum = pgEnum("user_status", ["active", "disabled"]);

export const jobStatusEnum = pgEnum("job_status", [
  "queued",
  "running",
  "waiting_input",
  "succeeded",
  "failed",
  "cancelled",
  "retrying"
]);

export const logLevelEnum = pgEnum("log_level", ["debug", "info", "warn", "error"]);

const jsonbEmptyObject = sql`'{}'::jsonb`;

export const users = pgTable(
  "users",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    email: varchar("email", { length: 320 }).notNull().unique(),
    name: varchar("name", { length: 120 }),
    passwordHash: text("password_hash"),
    role: roleEnum("role").notNull().default("user"),
    status: userStatusEnum("status").notNull().default("active"),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
    lastLoginAt: timestamp("last_login_at", { withTimezone: true })
  },
  (table) => [index("users_role_idx").on(table.role), index("users_status_idx").on(table.status)]
);

export const sessions = pgTable(
  "sessions",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    userId: uuid("user_id")
      .notNull()
      .references(() => users.id, { onDelete: "cascade" }),
    tokenHash: text("token_hash").notNull(),
    ip: varchar("ip", { length: 45 }),
    userAgent: text("user_agent"),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
    lastSeenAt: timestamp("last_seen_at", { withTimezone: true }),
    expiresAt: timestamp("expires_at", { withTimezone: true }).notNull(),
    revokedAt: timestamp("revoked_at", { withTimezone: true })
  },
  (table) => [
    index("sessions_user_id_idx").on(table.userId),
    index("sessions_token_hash_idx").on(table.tokenHash),
    index("sessions_expires_at_idx").on(table.expiresAt)
  ]
);

export const appSettings = pgTable(
  "app_settings",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    key: varchar("key", { length: 120 }).notNull().unique(),
    valueJson: jsonb("value_json").notNull().default(jsonbEmptyObject),
    updatedBy: uuid("updated_by").references(() => users.id, { onDelete: "set null" }),
    updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow()
  },
  (table) => [index("app_settings_updated_by_idx").on(table.updatedBy)]
);

export const auditLogs = pgTable(
  "audit_logs",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    actorId: uuid("actor_id").references(() => users.id, { onDelete: "set null" }),
    action: varchar("action", { length: 160 }).notNull(),
    entityType: varchar("entity_type", { length: 120 }).notNull(),
    entityId: uuid("entity_id"),
    ip: varchar("ip", { length: 45 }),
    metadataJson: jsonb("metadata_json").notNull().default(jsonbEmptyObject),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow()
  },
  (table) => [
    index("audit_logs_actor_id_idx").on(table.actorId),
    index("audit_logs_entity_idx").on(table.entityType, table.entityId),
    index("audit_logs_created_at_idx").on(table.createdAt)
  ]
);

export const jobs = pgTable(
  "jobs",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    queue: varchar("queue", { length: 120 }).notNull(),
    name: varchar("name", { length: 160 }).notNull(),
    bullmqJobId: varchar("bullmq_job_id", { length: 160 }),
    status: jobStatusEnum("status").notNull().default("queued"),
    progress: integer("progress").notNull().default(0),
    inputJson: jsonb("input_json").notNull().default(jsonbEmptyObject),
    resultJson: jsonb("result_json").notNull().default(jsonbEmptyObject),
    errorMessage: text("error_message"),
    createdBy: uuid("created_by").references(() => users.id, { onDelete: "set null" }),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
    startedAt: timestamp("started_at", { withTimezone: true }),
    finishedAt: timestamp("finished_at", { withTimezone: true })
  },
  (table) => [
    index("jobs_queue_status_idx").on(table.queue, table.status),
    index("jobs_created_by_idx").on(table.createdBy),
    index("jobs_created_at_idx").on(table.createdAt)
  ]
);

export const jobLogs = pgTable(
  "job_logs",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    jobId: uuid("job_id")
      .notNull()
      .references(() => jobs.id, { onDelete: "cascade" }),
    level: logLevelEnum("level").notNull().default("info"),
    message: text("message").notNull(),
    metadataJson: jsonb("metadata_json").notNull().default(jsonbEmptyObject),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow()
  },
  (table) => [
    index("job_logs_job_id_idx").on(table.jobId),
    index("job_logs_level_idx").on(table.level),
    index("job_logs_created_at_idx").on(table.createdAt)
  ]
);
