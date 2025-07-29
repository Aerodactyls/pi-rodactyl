import { readFile, writeFile } from "fs/promises";
import { join } from "path";
import { NextRequest, NextResponse } from "next/server";

const POSITIONS_FILE_PATH = join(process.cwd(), "lib", "positions.json");

export async function GET() {
  try {
    const data = await readFile(POSITIONS_FILE_PATH, "utf-8");
    return NextResponse.json(JSON.parse(data));
  } catch (error) {
    // If file doesn't exist, return empty positions
    if ((error as any).code === "ENOENT") {
      return NextResponse.json({});
    }
    console.error("Error reading positions file:", error);
    return NextResponse.json(
      { error: "Failed to read positions" },
      { status: 500 },
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const positions = await request.json();
    await writeFile(POSITIONS_FILE_PATH, JSON.stringify(positions, null, 2));
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error writing positions file:", error);
    return NextResponse.json(
      { error: "Failed to write positions" },
      { status: 500 },
    );
  }
}
