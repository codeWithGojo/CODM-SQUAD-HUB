# CoDM Squad Hub

CoDM Squad Hub is a cloud-native competitive Call of Duty: Mobile platform built for the African esports scene. It connects player identity, organizations, tournaments, official results, rankings, recruitment, training, media and AI-assisted performance workflows in one system.

## Current v6 development build

The latest mobile build includes:

- Expo / React Native mobile app with the purple esports design system
- Player Passport and competitive career history surfaces
- Tournament Control Centre and Match Centre flows
- Organization Owner HQ with T1–T4 roster management
- Player moves, role changes, contracts, stand-ins, staff permissions and applications
- AI Training plans, drill completion, coach controls and VOD-driven development flows
- Scrim Finder, scouting, free agents, tryouts and rankings
- Connection Check with gaming-focused ping/speed UX and Nigerian ISP coverage starter data
- Cloud-native architecture docs, Docker, Terraform and event-driven worker foundations

## Cloud architecture

The platform is designed around FastAPI, PostgreSQL/Supabase, Redis, object storage, queues/background workers, containerized workloads and Terraform-managed infrastructure. Tournament results and VOD analysis are designed as asynchronous event-driven workflows rather than blocking the mobile app.

## AI architecture

Squad Hub uses a hybrid model: deterministic esports intelligence for rankings/performance/scouting/chemistry, with Gemini as a reasoning and multimodal interpretation layer. AI is advisory; it does not set official rankings, resolve disputes or override admins.

## Why the network tools matter

Bad connection can literally cost an African CODM player a map or a tournament. Generic speed tests tell you Mbps; they do not tell you whether your connection is actually good enough for a competitive match. Connection Check is being built around gaming-relevant ping, stability, ISP coverage and regional reports.

## Built / Learned / Challenge

**Built:** a mobile-first esports operating system with cloud/event-driven foundations, competitive data flows, organization management and AI-assisted training.

**Learned:** reliable esports products need more than UI. Identity, auditability, asynchronous jobs, network quality and official-history integrity all affect the product architecture.

**Challenge:** Nigerian ISP data varies heavily by location and reliable public coverage/performance APIs are limited, so the system starts with curated coverage data and is structured to improve with verified user reports over time.

## Run the mobile app

```bash
cd frontend
npm install
npx expo start
```

## Status

This repository is an active development baseline, not a production release. Some screens and actions still use prototype/local state while backend persistence and production infrastructure are being connected.
