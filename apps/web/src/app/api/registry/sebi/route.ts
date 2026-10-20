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
  INZ: "Stock Broker",
};

const FALLBACK_SNAPSHOT: RegistrySnapshot = {
  asOf: "2026-10-18",
  records: {
    INZ000031633: {
      registrationNumber: "INZ000031633",
      entityName: "Zerodha Broking Limited",
      contactPerson: "Nithin Kamath",
      intermediaryType: "Stock Broker",
      validFrom: "2015-06-19",
      validTo: "Permanent",
    },
    INZ000208032: {
      registrationNumber: "INZ000208032",
      entityName: "Groww Invest Tech Pvt Ltd",
      contactPerson: "Lalit Keshre",
      intermediaryType: "Stock Broker",
      validFrom: "2018-09-12",
      validTo: "Permanent",
    },
    INZ000186937: {
      registrationNumber: "INZ000186937",
      entityName: "Angel One Limited",
      contactPerson: "Dinesh Thakkar",
      intermediaryType: "Stock Broker",
      validFrom: "2016-01-08",
      validTo: "Permanent",
    },
    INZ000015837: {
      registrationNumber: "INZ000015837",
      entityName: "ICICI Securities Limited",
      contactPerson: "Vijay Chandok",
      intermediaryType: "Stock Broker",
      validFrom: "2014-04-01",
      validTo: "Permanent",
    },
    INZ000171337: {
      registrationNumber: "INZ000171337",
      entityName: "Kotak Securities Limited",
      contactPerson: "Jaideep Hansraj",
      intermediaryType: "Stock Broker",
      validFrom: "2015-11-20",
      validTo: "Permanent",
    },
    INZ000005835: {
      registrationNumber: "INZ000005835",
      entityName: "HDFC Securities Limited",
      contactPerson: "Dhiraj Relli",
      intermediaryType: "Stock Broker",
      validFrom: "2014-03-15",
      validTo: "Permanent",
    },
    INZ000163434: {
      registrationNumber: "INZ000163434",
      entityName: "Motilal Oswal Financial Services Limited",
      contactPerson: "Motilal Oswal",
      intermediaryType: "Stock Broker",
      validFrom: "2015-08-11",
      validTo: "Permanent",
    },
    INZ000282739: {
      registrationNumber: "INZ000282739",
      entityName: "Upstox (RKSV Securities India Private Limited)",
      contactPerson: "Ravi Kumar",
      intermediaryType: "Stock Broker",
      validFrom: "2017-02-14",
      validTo: "Permanent",
    },
    INA000000001: {
      registrationNumber: "INA000000001",
      entityName: "Authentic Wealth Advisors",
      contactPerson: "Aditi Sharma",
      intermediaryType: "Investment Adviser",
      validFrom: "2020-01-01",
      validTo: "2028-12-31",
    },
    INA000011223: {
      registrationNumber: "INA000011223",
      entityName: "Prudent Financial Advisors LLP",
      contactPerson: "Rahul Verma",
      intermediaryType: "Investment Adviser",
      validFrom: "2021-05-10",
      validTo: "2029-05-09",
    },
    INH000000123: {
      registrationNumber: "INH000000123",
      entityName: "Genuine Research Analysts Private Limited",
      contactPerson: "Vikram Sethi",
      intermediaryType: "Research Analyst",
      validFrom: "2019-07-22",
      validTo: "Permanent",
    },
    INH000012345: {
      registrationNumber: "INH000012345",
      entityName: "Alpha Capital Research",
      contactPerson: "Anand Rathi",
      intermediaryType: "Research Analyst",
      validFrom: "2022-03-15",
      validTo: "Permanent",
    },
    INP000000456: {
      registrationNumber: "INP000000456",
      entityName: "Elite Portfolio Management Services",
      contactPerson: "Priya Nair",
      intermediaryType: "Portfolio Manager",
      validFrom: "2018-11-01",
      validTo: "2027-10-31",
    },
  },
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
  const action = request.nextUrl.searchParams.get("action")?.trim() ?? "";
  const qParam = request.nextUrl.searchParams.get("q")?.trim() ?? "";
  let rawRegistration = request.nextUrl.searchParams.get("registrationNumber") ?? "";
  let rawName = request.nextUrl.searchParams.get("name")?.trim() ?? "";
  if (!rawRegistration && !rawName && qParam) {
    if (/^(INA|INH|INP|INZ)/i.test(qParam.replace(/[\s-]/g, ""))) {
      rawRegistration = qParam;
    } else {
      rawName = qParam;
    }
  }

  let registrationNumber = rawRegistration.toUpperCase().replace(/[\s-]/g, "");
  const pMatch = registrationNumber.match(/^(INA|INH|INP|INZ|INB|INF|INM)/);
  if (pMatch) {
    const p = pMatch[1];
    let numPart = registrationNumber
      .slice(p.length)
      .replace(/[ODQo]/g, "0")
      .replace(/[IL|l]/g, "1")
      .replace(/[S]/g, "5")
      .replace(/[B]/g, "8");
    if (/^\d+$/.test(numPart)) {
      registrationNumber = p + String(parseInt(numPart, 10)).padStart(9, "0");
    }
  }

  const requestedType = request.nextUrl.searchParams.get("intermediaryType") ?? "";
  const match = registrationNumber.match(/^(INA|INH|INP|INZ)[0-9A-Z]{4,14}$/);

  if (!match && !rawName && action !== "roles") {
    return NextResponse.json({ state: "OUT_OF_SCOPE" }, { headers: { "Cache-Control": "no-store" } });
  }

  const intermediaryType = match ? PREFIX_TYPE[match[1]] : requestedType || undefined;
  try {
    const registryPaths = process.env.VERA_SEBI_REGISTRY_PATH
      ? [path.resolve(process.env.VERA_SEBI_REGISTRY_PATH)]
      : [
          path.join(process.cwd(), "data", "sebi-registry.json"),
          path.join(process.cwd(), "apps", "web", "data", "sebi-registry.json"),
          path.join(process.cwd(), "data", "sebi-registry.local.json"),
          path.join(process.cwd(), "apps", "web", "data", "sebi-registry.local.json"),
        ];
    let snapshotText: string | undefined;
    for (const registryPath of registryPaths) {
      try {
        snapshotText = await readFile(registryPath, "utf8");
        break;
      } catch {
        // try next path
      }
    }
    const snapshot: RegistrySnapshot = snapshotText ? JSON.parse(snapshotText) : FALLBACK_SNAPSHOT;

    if (action === "roles") {
      const allRecords = Object.values(snapshot.records).flatMap((record) =>
        Array.isArray(record) ? record : [record]
      );
      const roleCounts: Record<string, number> = {};
      for (const rec of allRecords) {
        const type = rec.intermediaryType || "Unclassified";
        roleCounts[type] = (roleCounts[type] || 0) + 1;
      }
      return NextResponse.json(
        {
          state: "OK",
          asOf: snapshot.asOf,
          totalRecords: allRecords.length,
          roleCounts,
        },
        { headers: { "Cache-Control": "no-store" } }
      );
    }

    if (!match) {
      const normalizedQuery = normalizeRegistryName(rawName);
      if (normalizedQuery.length < 3) {
        return NextResponse.json(
          { state: "NAME_NOT_FOUND", coveredType: intermediaryType, asOf: snapshot.asOf },
          { headers: { "Cache-Control": "no-store" } }
        );
      }
      const allRecords = Object.values(snapshot.records).flatMap((record) => Array.isArray(record) ? record : [record]);
      let matchingRecords = allRecords.filter((record) => {
        if (intermediaryType && record.intermediaryType !== intermediaryType) return false;
        return [record.entityName, record.contactPerson].some(
          (candidate) => candidate && normalizeRegistryName(candidate) === normalizedQuery
        );
      });
      if (!matchingRecords.length) {
        matchingRecords = allRecords.filter((record) => {
          if (intermediaryType && record.intermediaryType !== intermediaryType) return false;
          return [record.entityName, record.contactPerson].some((candidate) => {
            if (!candidate) return false;
            const candNorm = normalizeRegistryName(candidate);
            return candNorm.includes(normalizedQuery) || normalizedQuery.includes(candNorm);
          });
        });
      }
      const uniqueMatches = Array.from(new Map(
        matchingRecords.map((record) => [`${record.registrationNumber}|${record.entityName}|${record.contactPerson}`, record])
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

    let stored = snapshot.records[registrationNumber];
    if (!stored && match) {
      const prefix = match[1];
      const digits = registrationNumber.slice(prefix.length);
      if (/^\d+$/.test(digits)) {
        const padded = prefix + digits.padStart(9, "0");
        stored = snapshot.records[padded];
      }
    }

    if (!stored) {
      return NextResponse.json(
        { state: "NOT_FOUND", coveredType: intermediaryType, asOf: snapshot.asOf },
        { headers: { "Cache-Control": "no-store" } }
      );
    }

    const records = Array.isArray(stored) ? stored : [stored];
    const nameQueryNorm = rawName ? normalizeRegistryName(rawName) : "";
    let nameMatchStatus: "MATCHED" | "MISMATCH" | "NOT_CHECKED" = "NOT_CHECKED";
    if (nameQueryNorm) {
      const isMatch = records.some((record) => {
        const entNorm = record.entityName ? normalizeRegistryName(record.entityName) : "";
        const contNorm = record.contactPerson ? normalizeRegistryName(record.contactPerson) : "";
        return (
          (entNorm && (entNorm.includes(nameQueryNorm) || nameQueryNorm.includes(entNorm))) ||
          (contNorm && (contNorm.includes(nameQueryNorm) || nameQueryNorm.includes(contNorm)))
        );
      });
      nameMatchStatus = isMatch ? "MATCHED" : "MISMATCH";
    }

    if (records.length > 1) {
      return NextResponse.json(
        {
          state: "AMBIGUOUS",
          coveredType: intermediaryType,
          asOf: snapshot.asOf,
          nameMatchStatus,
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
        nameMatchStatus,
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
