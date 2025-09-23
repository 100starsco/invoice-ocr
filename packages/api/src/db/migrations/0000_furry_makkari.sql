CREATE TABLE "jobs" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"job_id" varchar(255) NOT NULL,
	"queue_name" varchar(100) NOT NULL,
	"job_name" varchar(255) NOT NULL,
	"status" varchar(50) DEFAULT 'pending' NOT NULL,
	"priority" integer DEFAULT 0,
	"attempts" integer DEFAULT 0,
	"max_attempts" integer DEFAULT 3,
	"data" jsonb,
	"result" jsonb,
	"error" jsonb,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL,
	"started_at" timestamp,
	"completed_at" timestamp,
	"failed_at" timestamp,
	"processing_time_ms" integer,
	"worker_instance" varchar(255),
	"parent_job_id" uuid,
	"metadata" jsonb,
	CONSTRAINT "jobs_job_id_unique" UNIQUE("job_id")
);
--> statement-breakpoint
CREATE TABLE "line_events" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"event_type" varchar(50) NOT NULL,
	"event_id" varchar(255),
	"reply_token" varchar(255),
	"user_id" varchar(100),
	"group_id" varchar(100),
	"room_id" varchar(100),
	"event_data" jsonb NOT NULL,
	"webhook_id" varchar(255),
	"processed" boolean DEFAULT false,
	"processing_started_at" timestamp,
	"processing_completed_at" timestamp,
	"processing_error" text,
	"job_id" uuid,
	"received_at" timestamp DEFAULT now() NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "line_messages" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"message_id" varchar(255) NOT NULL,
	"message_type" varchar(50) NOT NULL,
	"content" jsonb NOT NULL,
	"user_id" varchar(100) NOT NULL,
	"event_id" uuid,
	"reply_token" varchar(255),
	"responded" boolean DEFAULT false,
	"response_type" varchar(50),
	"response_job_id" uuid,
	"sent_at" timestamp NOT NULL,
	"received_at" timestamp DEFAULT now() NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL,
	CONSTRAINT "line_messages_message_id_unique" UNIQUE("message_id")
);
--> statement-breakpoint
CREATE TABLE "line_users" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" varchar(100) NOT NULL,
	"display_name" varchar(255),
	"picture_url" varchar(500),
	"status_message" text,
	"language" varchar(10),
	"is_following" boolean DEFAULT true,
	"is_blocked" boolean DEFAULT false,
	"profile_last_updated" timestamp,
	"first_seen_at" timestamp DEFAULT now() NOT NULL,
	"last_seen_at" timestamp DEFAULT now() NOT NULL,
	"last_message_at" timestamp,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL,
	CONSTRAINT "line_users_user_id_unique" UNIQUE("user_id")
);
--> statement-breakpoint
ALTER TABLE "jobs" ADD CONSTRAINT "jobs_parent_job_id_jobs_id_fk" FOREIGN KEY ("parent_job_id") REFERENCES "public"."jobs"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "line_events" ADD CONSTRAINT "line_events_job_id_jobs_id_fk" FOREIGN KEY ("job_id") REFERENCES "public"."jobs"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "line_messages" ADD CONSTRAINT "line_messages_event_id_line_events_id_fk" FOREIGN KEY ("event_id") REFERENCES "public"."line_events"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "line_messages" ADD CONSTRAINT "line_messages_response_job_id_jobs_id_fk" FOREIGN KEY ("response_job_id") REFERENCES "public"."jobs"("id") ON DELETE no action ON UPDATE no action;