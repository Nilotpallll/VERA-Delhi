import { NextRequest, NextResponse } from "next/server";
import { readFile } from "node:fs/promises";
import path from "node:path";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

type RegistryRecord = {
  registrationNumber: string;
  entityName: string;
  contactPerson: string;
  intermediaryType: string;
  validFrom: string;
  validTo: string;
};

type RegistrySnapshot = {
  asOf: string;
  records: Record<string, RegistryRecord | RegistryRecord[]>;
};

const PREFIX_TYPE: Record<string, string> = {
  INA: "Investment Adviser",
  INH: "Research Analyst",
  INP: "Portfolio Manager",
};

function normalizeRegistryName(value: string): string {
  return value
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase()
    .replace(/^(mr|mrs|ms|miss|dr)\.?\s+/, "")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .trim()
    .replace(/\s+/g, " ");
}

export async function GET(request: NextRequest) {
  const rawRegistration = request.nextUrl.searchParams.get("registrationNumber") ?? "";
  const registrationNumber = rawRegistration.toUpperCase().replace(/[\s-]/g, "");
  const rawName = request.nextUrl.searchParams.get("name")?.trim() ?? "";
  const requestedType = request.nextUrl.searchParams.get("intermediaryType") ?? "";
  const match = registrationNumber.match(/^(INA|INH|INP)[0-9A-Z]{8,10}$/);

  if (!match && !rawName) {
    return NextResponse.json({ state: "OUT_OF_SCOPE" }, { headers: { "Cache-Control": "no-store" } });
  }

  const intermediaryType = match ? PREFIX_TYPE[match[1]] : requestedType || undefined;
  try {
    const registryPaths = process.env.VERA_SEBI_REGISTRY_PATH
      ? [path.resolve(process.env.VERA_SEBI_REGISTRY_PATH)]
      : [
          path.join(process.cwd(), "data", "sebi-registry.local.json"),
          path.join(process.cwd(), "apps", "web", "data", "sebi-registry.local.json"),
        ];
    let snapshotText: string | undefined;
    let lastReadError: unknown;
    for (const registryPath of registryPaths) {
      try {
        snapshotText = await readFile(registryPath, "utf8");
        break;
      } catch (error) {
        lastReadError = error;
      }
    }
    if (!snapshotText) throw lastReadError ?? new Error("Registry snapshot file is empty");
    const snapshot = JSON.parse(snapshotText) as RegistrySnapshot;

    if (!match) {
      const normalizedQuery = normalizeRegistryName(rawName);
      if (normalizedQuery.length < 3) {
        return NextResponse.json(
          { state: "NAME_NOT_FOUND", coveredType: intermediaryType, asOf: snapshot.asOf },
          { headers: { "Cache-Control": "no-store" } }
        );
      }
      const allRecords = Object.values(snapshot.records).flatMap((record) => Array.isArray(record) ? record : [record]);
      const exactMatches = allRecords.filter((record) => {
        if (intermediaryType && record.intermediaryType !== intermediaryType) return false;
        return [record.entityName, record.contactPerson].some(
          (candidate) => candidate && normalizeRegistryName(candidate) === normalizedQuery
        );
      });
      const uniqueMatches = Array.from(new Map(
        exactMatches.map((record) => [`${record.registrationNumber}|${record.entityName}|${record.contactPerson}`, record])
      ).values());
      if (!uniqueMatches.length) {
        return NextResponse.json(
          { state: "NAME_NOT_FOUND", coveredType: intermediaryType, asOf: snapshot.asOf },
          { headers: { "Cache-Control": "no-store" } }
        );
      }
      const resultRecords = uniqueMatches.slice(0, 6);
      return NextResponse.json(
        {
          state: uniqueMatches.length > 1 ? "AMBIGUOUS" : "FOUND",
          lookupBy: "EXACT_NAME",
          coveredType: intermediaryType,
          asOf: snapshot.asOf,
          records: resultRecords.map((record) => ({
            registrationNumber: record.registrationNumber,
            entityName: record.entityName,
            contactPerson: record.contactPerson,
            intermediaryType: record.intermediaryType,
            validFrom: record.validFrom,
            validTo: record.validTo,
          })),
        },
        { headers: { "Cache-Control": "no-store" } }
      );
    }

    const stored = snapshot.records[registrationNumber];

    if (!stored) {
      return NextResponse.json(
        { state: "NOT_FOUND", coveredType: intermediaryType, asOf: snapshot.asOf },
        { headers: { "Cache-Control": "no-store" } }
      );
    }

    const records = Array.isArray(stored) ? stored : [stored];
    if (records.length > 1) {
      return NextResponse.json(
        {
          state: "AMBIGUOUS",
          coveredType: intermediaryType,
          asOf: snapshot.asOf,
          records: records.map((record) => ({
            registrationNumber: record.registrationNumber,
            entityName: record.entityName,
            contactPerson: record.contactPerson,
            intermediaryType: record.intermediaryType,
            validFrom: record.validFrom,
            validTo: record.validTo,
          })),
        },
        { headers: { "Cache-Control": "no-store" } }
      );
    }

    return NextResponse.json(
      {
        state: "FOUND",
        coveredType: intermediaryType,
        asOf: snapshot.asOf,
        records: records.map((record) => ({
          registrationNumber: record.registrationNumber,
          entityName: record.entityName,
          contactPerson: record.contactPerson,
          intermediaryType: record.intermediaryType,
          validFrom: record.validFrom,
          validTo: record.validTo,
        })),
      },
      { headers: { "Cache-Control": "no-store" } }
    );
  } catch (error) {
    console.error("Local SEBI registry snapshot is unavailable:", error);
    return NextResponse.json(
      { state: "UNAVAILABLE", coveredType: intermediaryType },
      { status: 503, headers: { "Cache-Control": "no-store" } }
    );
  }
}
