export interface GameAnalysis {
  id: string;
  name: string;
  steamAppId?: number;
  analysis: string;
  tags: string[];
  score: number;
  createdAt: string;
}

export interface MarketingPlan {
  id: string;
  gameId: string;
  strategy: string;
  pitch: string;
  tags: string[];
  createdAt: string;
}

export interface StreamerMatch {
  id: string;
  streamerName: string;
  platform: string;
  matchScore: number;
  reason: string;
}
