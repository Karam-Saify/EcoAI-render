import React, { useEffect, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  Activity,
  Building2,
  Filter,
  Globe2,
  MapPinned,
  Network,
  RefreshCw,
  ShieldCheck,
  Target,
  Users,
} from 'lucide-react';

type Overview = {
  entity_composition: Array<{ name: string; value: number }>;
  top_kpis: {
    total_investors: number;
    total_projects: number;
    total_volunteers: number;
    total_ngos: number;
    total_matches: number;
    avg_match_score: number;
  };
  regional_distribution: Array<{ region: string; Projects: number; Investors: number; Volunteers: number; NGOs: number }>;
  top_sectors: Array<{ name: string; val: number }>;
  match_coverage: Array<{ entity: string; matched_projects: number; avg_top_score: number }>;
  stage_distribution: Array<{ name: string; val: number }>;
};

type Entities = {
  investor_risk_reporting_matrix: number[][];
  project_sector_stage_heatmap: { xAxis: string[]; yAxis: string[]; data: Array<[number, number, number]> };
  skill_demand_supply: Array<{ skill: string; demand: number; supply: number }>;
  funding_histogram: Array<{ band: string; count: number }>;
  top_project_geographies: Array<{ name: string; val: number }>;
  activity_geography_map: {
    points: Array<{
      id: string;
      code: string;
      name: string;
      place_type: 'country' | 'region';
      lat: number | null;
      lon: number | null;
      activity_count: number;
      project_count: number;
      volunteer_count: number;
      investor_count: number;
      ecosystem_total: number;
      results_count: number;
      is_mappable: boolean;
      dominant_sector: string;
      sector_counts: Record<string, number>;
      sector_breakdown: Array<{ name: string; value: number }>;
      sample_organizations: string[];
    }>;
    filters: {
      sectors: string[];
      layers: Array<'activity_count' | 'ecosystem_total' | 'project_count' | 'volunteer_count' | 'investor_count'>;
      place_types: Array<'country' | 'region'>;
    };
    summary: {
      tracked_activities: number;
      mapped_locations: number;
      distinct_places: number;
      unlocated_activities: number;
      top_activity_location: { name: string; count: number };
      top_ecosystem_location: { name: string; count: number };
    };
  };
};

type Clusters = {
  umap_nodes: Array<{ id: number; x: number; y: number; type: string; name?: string; sector?: string; region?: string }>;
  semantic_map: Array<{ id: number; x: number; y: number; type: string; name: string; sector: string; region: string }>;
  match_corridors: Array<{
    sector: string;
    projects: number;
    avg_investor_score: number;
    avg_volunteer_score: number;
    avg_grant_score: number;
    avg_precedent_score: number;
    fit_index: number;
    sample_projects: string[];
  }>;
  match_network: {
    nodes: Array<{ id: string; name: string; value: number; group: string; subtitle?: string; score?: number }>;
    edges: Array<{ source: string; target: string; value: number; relation: string; rationale: string }>;
    summary: {
      projects: number;
      connections: number;
      avg_score: number;
      investor_edges: number;
      volunteer_edges: number;
      grant_edges: number;
      precedent_edges: number;
    };
  };
  project_match_panels: Array<{
    project_id: string;
    project_title: string;
    sector: string;
    stage: string;
    country: string;
    investor: { name: string; score: number; rationale: string } | null;
    volunteer: { name: string; score: number; rationale: string } | null;
    grant: { name: string; score: number; rationale: string } | null;
    precedent: { name: string; score: number; rationale: string } | null;
  }>;
  cluster_signal: { lead_sector: string; fit_index: number; narrative: string };
};

const COLORS = {
  bg: '#08111f',
  panel: 'rgba(19,34,56,0.86)',
  panelSoft: 'rgba(15,27,45,0.78)',
  border: '#243754',
  text: '#ecf2f8',
  textSoft: '#9fb0c7',
  textDim: '#6f829c',
  projects: '#19c28f',
  investors: '#4f7cff',
  volunteers: '#8a7cf7',
  ngos: '#c89a3d',
  teal: '#0ea5a4',
};

const palette = [COLORS.projects, COLORS.investors, COLORS.volunteers, COLORS.ngos, COLORS.teal, '#d45757'];
const shellBg =
  'min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(25,194,143,0.08),_transparent_28%),linear-gradient(180deg,#08111f_0%,#0d1728_52%,#101a2c_100%)] text-slate-100 p-6 md:p-10';
const cardClass = 'rounded-3xl border border-[#243754] bg-[rgba(19,34,56,0.86)] p-6 shadow-2xl shadow-black/20';
const metricCardClass = 'rounded-2xl border border-[#243754] bg-[rgba(19,34,56,0.86)] p-5 shadow-2xl shadow-black/20';
const geoBounds = { minLat: -55, maxLat: 80, width: 1000, height: 520 };
const geoLayerMeta = {
  activity_count: { label: 'Activities', tone: COLORS.projects },
  ecosystem_total: { label: 'Ecosystem Total', tone: '#56d5d0' },
  project_count: { label: 'Projects', tone: COLORS.investors },
  volunteer_count: { label: 'Volunteers', tone: COLORS.volunteers },
  investor_count: { label: 'Investors', tone: COLORS.ngos },
} as const;
const apiBaseUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');

function geoMetricValue(point: Entities['activity_geography_map']['points'][number], layer: keyof typeof geoLayerMeta) {
  return point[layer];
}

function projectGeoPoint(lat: number, lon: number) {
  const clampedLat = Math.min(geoBounds.maxLat, Math.max(geoBounds.minLat, lat));
  return {
    x: ((lon + 180) / 360) * geoBounds.width,
    y: ((geoBounds.maxLat - clampedLat) / (geoBounds.maxLat - geoBounds.minLat)) * geoBounds.height,
  };
}

function HeatCell({ value, max }: { value: number; max: number }) {
  const intensity = max > 0 ? value / max : 0;
  return (
    <div
      className="rounded-lg border border-[#243754] p-3 text-center text-sm text-[#ecf2f8]"
      style={{ backgroundColor: `rgba(25,194,143,${0.12 + intensity * 0.7})` }}
    >
      {value}
    </div>
  );
}

function App() {
  const [activeTab, setActiveTab] = useState<'overview' | 'entities' | 'clusters' | 'geography'>('overview');
  const [overview, setOverview] = useState<Overview | null>(null);
  const [entities, setEntities] = useState<Entities | null>(null);
  const [clusters, setClusters] = useState<Clusters | null>(null);
  const [loading, setLoading] = useState(true);
  const [geoLayer, setGeoLayer] = useState<keyof typeof geoLayerMeta>('activity_count');
  const [geoPlaceType, setGeoPlaceType] = useState<'all' | 'country' | 'region'>('all');
  const [geoSector, setGeoSector] = useState('All sectors');
  const [selectedGeoId, setSelectedGeoId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const loadData = async () => {
      setLoading(true);
      try {
        const [overviewRes, entitiesRes, clustersRes] = await Promise.all([
          fetch(`${apiBaseUrl}/api/v2/analytics/overview`),
          fetch(`${apiBaseUrl}/api/v2/analytics/entities`),
          fetch(`${apiBaseUrl}/api/v2/analytics/clusters`),
        ]);
        if (!cancelled) {
          if (overviewRes.ok) setOverview(await overviewRes.json());
          if (entitiesRes.ok) setEntities(await entitiesRes.json());
          if (clustersRes.ok) setClusters(await clustersRes.json());
        }
      } catch (error) {
        console.error(error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    loadData();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!entities?.activity_geography_map.points.length) {
      return;
    }
    if (!selectedGeoId || !entities.activity_geography_map.points.some((point) => point.id === selectedGeoId)) {
      setSelectedGeoId(entities.activity_geography_map.points[0].id);
    }
  }, [entities, selectedGeoId]);

  if (!overview || !entities || !clusters) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: COLORS.bg, color: COLORS.text }}>
        <div className="flex items-center gap-3 text-sm tracking-wide" style={{ color: COLORS.textSoft }}>
          <RefreshCw className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} style={{ color: COLORS.projects }} />
          Booting Ecowise intelligence surfaces...
        </div>
      </div>
    );
  }

  const sectorHeatMax = Math.max(...entities.project_sector_stage_heatmap.data.map((item) => item[2]), 1);
  const investorMatrixMax = Math.max(...entities.investor_risk_reporting_matrix.flat(), 1);
  const semanticGroups = Array.from(new Set(clusters.semantic_map.map((node) => node.type)));
  const matchNodeMap = new Map(clusters.match_network.nodes.map((node) => [node.id, node]));
  const matchEdgeRows = clusters.match_network.edges
    .map((edge) => ({
      ...edge,
      sourceName: matchNodeMap.get(edge.source)?.name || edge.source,
      targetName: matchNodeMap.get(edge.target)?.name || edge.target,
    }))
    .sort((left, right) => right.value - left.value);
  const geoMap = entities.activity_geography_map;
  const filteredGeoPoints = [...geoMap.points]
    .filter((point) => geoPlaceType === 'all' || point.place_type === geoPlaceType)
    .filter((point) => geoSector === 'All sectors' || (point.sector_counts[geoSector] ?? 0) > 0)
    .sort((left, right) => {
      const metricGap = geoMetricValue(right, geoLayer) - geoMetricValue(left, geoLayer);
      if (metricGap !== 0) {
        return metricGap;
      }
      return right.activity_count - left.activity_count;
    });
  const mappedGeoPoints = filteredGeoPoints.filter((point) => point.is_mappable && geoMetricValue(point, geoLayer) > 0);
  const activeGeoPoint = filteredGeoPoints.find((point) => point.id === selectedGeoId) ?? filteredGeoPoints[0] ?? null;
  const topGeoLabelIds = filteredGeoPoints.slice(0, 8).map((point) => point.id);
  const maxGeoMetric = Math.max(...mappedGeoPoints.map((point) => geoMetricValue(point, geoLayer)), 1);

  return (
    <div className={shellBg}>
      <header className="mb-8 flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
        <div className="max-w-2xl">
          <p className="mb-3 text-xs uppercase tracking-[0.35em]" style={{ color: COLORS.projects }}>
            Ecowise Internal Intelligence
          </p>
          <h1 className="text-4xl font-semibold tracking-tight text-white">Executive sustainability matching command center</h1>
          <p className="mt-3 text-sm leading-7" style={{ color: COLORS.textSoft }}>
            Canonical ecosystem analytics across projects, investors, volunteers, grants, and external precedents.
          </p>
        </div>
        <div className="inline-flex rounded-2xl border bg-[rgba(15,27,45,0.88)] p-1" style={{ borderColor: COLORS.border }}>
          {[
            ['overview', 'Executive Overview'],
            ['entities', 'Entity Intelligence'],
            ['clusters', 'Matching & Clusters'],
            ['geography', 'Geographic Activity'],
          ].map(([value, label]) => (
            <button
              key={value}
              onClick={() => setActiveTab(value as typeof activeTab)}
              className="rounded-xl px-4 py-3 text-sm transition"
              style={
                activeTab === value
                  ? { backgroundColor: COLORS.text, color: COLORS.bg }
                  : { color: COLORS.textSoft }
              }
            >
              {label}
            </button>
          ))}
        </div>
      </header>

      <section className="mb-8 grid grid-cols-2 gap-4 xl:grid-cols-6">
        {[
          { label: 'Projects', value: overview.top_kpis.total_projects, icon: Target, tone: COLORS.projects },
          { label: 'Investors', value: overview.top_kpis.total_investors, icon: ShieldCheck, tone: COLORS.investors },
          { label: 'Volunteers', value: overview.top_kpis.total_volunteers, icon: Users, tone: COLORS.volunteers },
          { label: 'NGOs', value: overview.top_kpis.total_ngos, icon: Globe2, tone: COLORS.ngos },
          { label: 'Matches', value: overview.top_kpis.total_matches, icon: Network, tone: '#56d5d0' },
          { label: 'Avg Score', value: overview.top_kpis.avg_match_score, icon: Activity, tone: '#7fe2b5' },
        ].map((item) => (
          <div key={item.label} className={metricCardClass}>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.25em]" style={{ color: COLORS.textDim }}>
                  {item.label}
                </p>
                <p className="mt-3 text-3xl font-light" style={{ color: item.tone }}>
                  {item.value}
                </p>
              </div>
              <item.icon className="h-5 w-5" style={{ color: item.tone }} />
            </div>
          </div>
        ))}
      </section>

      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="grid gap-6 xl:grid-cols-[1.1fr_1.5fr_1fr]">
            <div className={cardClass}>
              <p className="mb-4 text-sm" style={{ color: COLORS.text }}>
                Platform composition
              </p>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={overview.entity_composition} dataKey="value" nameKey="name" innerRadius={68} outerRadius={102}>
                      {overview.entity_composition.map((entry, index) => (
                        <Cell key={entry.name} fill={palette[index % palette.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className={cardClass}>
              <p className="mb-4 text-sm" style={{ color: COLORS.text }}>
                Regional concentration matrix
              </p>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={overview.regional_distribution}>
                    <CartesianGrid stroke={COLORS.border} strokeDasharray="3 3" />
                    <XAxis type="number" stroke={COLORS.textDim} />
                    <YAxis type="category" dataKey="region" stroke={COLORS.textSoft} width={100} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="Projects" stackId="a" fill={COLORS.projects} />
                    <Bar dataKey="Investors" stackId="a" fill={COLORS.investors} />
                    <Bar dataKey="Volunteers" stackId="a" fill={COLORS.volunteers} />
                    <Bar dataKey="NGOs" stackId="a" fill={COLORS.ngos} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className={cardClass}>
              <p className="mb-5 text-sm" style={{ color: COLORS.text }}>
                Top functional sectors
              </p>
              <div className="space-y-4">
                {overview.top_sectors.map((sector) => {
                  const max = Math.max(...overview.top_sectors.map((item) => item.val), 1);
                  return (
                    <div key={sector.name} className="flex items-center gap-3">
                      <div className="w-28 truncate text-right text-sm" style={{ color: COLORS.textSoft }}>
                        {sector.name}
                      </div>
                      <div className="h-2 flex-1 rounded-full bg-[#1a2b45]">
                        <div
                          className="h-2 rounded-full"
                          style={{ width: `${Math.max(6, (sector.val / max) * 100)}%`, backgroundColor: COLORS.projects }}
                        />
                      </div>
                      <div className="w-9 text-right font-mono text-xs" style={{ color: COLORS.text }}>
                        {sector.val}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="grid gap-6 xl:grid-cols-2">
            <div className={cardClass}>
              <p className="mb-4 text-sm" style={{ color: COLORS.text }}>
                Match coverage by entity type
              </p>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={overview.match_coverage} layout="vertical">
                    <CartesianGrid stroke={COLORS.border} strokeDasharray="3 3" />
                    <XAxis type="number" stroke={COLORS.textDim} />
                    <YAxis type="category" dataKey="entity" stroke={COLORS.textSoft} width={96} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="matched_projects" fill={COLORS.investors} />
                    <Bar dataKey="avg_top_score" fill={COLORS.ngos} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className={cardClass}>
              <p className="mb-4 text-sm" style={{ color: COLORS.text }}>
                Project stage distribution
              </p>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={overview.stage_distribution}>
                    <CartesianGrid stroke={COLORS.border} strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke={COLORS.textSoft} />
                    <YAxis stroke={COLORS.textDim} />
                    <Tooltip />
                    <Bar dataKey="val" fill={COLORS.projects} radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'entities' && (
        <div className="grid gap-6 xl:grid-cols-2">
          <div className="space-y-6">
            <div className={cardClass}>
              <p className="mb-4 text-sm" style={{ color: COLORS.text }}>
                Project pipeline heatmap
              </p>
              <div className="grid gap-3" style={{ gridTemplateColumns: `110px repeat(${entities.project_sector_stage_heatmap.xAxis.length}, minmax(0, 1fr))` }}>
                <div />
                {entities.project_sector_stage_heatmap.xAxis.map((stage) => (
                  <div key={stage} className="text-center text-xs uppercase tracking-[0.2em]" style={{ color: COLORS.textDim }}>
                    {stage}
                  </div>
                ))}
                {entities.project_sector_stage_heatmap.yAxis.map((sector, rowIndex) => (
                  <React.Fragment key={sector}>
                    <div className="flex items-center text-sm" style={{ color: COLORS.textSoft }}>
                      {sector}
                    </div>
                    {entities.project_sector_stage_heatmap.xAxis.map((_, colIndex) => {
                      const point = entities.project_sector_stage_heatmap.data.find((item) => item[0] === colIndex && item[1] === rowIndex);
                      return <HeatCell key={`${sector}-${colIndex}`} value={point ? point[2] : 0} max={sectorHeatMax} />;
                    })}
                  </React.Fragment>
                ))}
              </div>
            </div>

            <div className={cardClass}>
              <p className="mb-4 text-sm" style={{ color: COLORS.text }}>
                Volunteer demand vs supply
              </p>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={entities.skill_demand_supply} layout="vertical">
                    <CartesianGrid stroke={COLORS.border} strokeDasharray="3 3" />
                    <XAxis type="number" stroke={COLORS.textDim} />
                    <YAxis type="category" dataKey="skill" stroke={COLORS.textSoft} width={120} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="demand" fill={COLORS.ngos} />
                    <Bar dataKey="supply" fill={COLORS.investors} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className={cardClass}>
              <p className="mb-4 text-sm" style={{ color: COLORS.text }}>
                Project funding bands
              </p>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={entities.funding_histogram}>
                    <CartesianGrid stroke={COLORS.border} strokeDasharray="3 3" />
                    <XAxis dataKey="band" stroke={COLORS.textSoft} />
                    <YAxis stroke={COLORS.textDim} />
                    <Tooltip />
                    <Bar dataKey="count" fill={COLORS.teal} radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className={cardClass}>
              <p className="mb-4 text-sm" style={{ color: COLORS.text }}>
                Investor risk x reporting burden
              </p>
              <div className="grid grid-cols-[90px_repeat(3,minmax(0,1fr))] gap-3">
                <div />
                {['Low', 'Med', 'High'].map((label) => (
                  <div key={label} className="text-center text-xs uppercase tracking-[0.2em]" style={{ color: COLORS.textDim }}>
                    {label}
                  </div>
                ))}
                {['Low', 'Med', 'High'].map((riskLabel, rowIndex) => (
                  <React.Fragment key={riskLabel}>
                    <div className="flex items-center text-sm" style={{ color: COLORS.textSoft }}>
                      {riskLabel}
                    </div>
                    {entities.investor_risk_reporting_matrix[rowIndex].map((value, colIndex) => (
                      <HeatCell key={`${riskLabel}-${colIndex}`} value={value} max={investorMatrixMax} />
                    ))}
                  </React.Fragment>
                ))}
              </div>
            </div>

            <div className={cardClass}>
              <p className="mb-4 text-sm" style={{ color: COLORS.text }}>
                Top project geographies
              </p>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={entities.top_project_geographies} layout="vertical">
                    <CartesianGrid stroke={COLORS.border} strokeDasharray="3 3" />
                    <XAxis type="number" stroke={COLORS.textDim} />
                    <YAxis type="category" dataKey="name" stroke={COLORS.textSoft} width={90} />
                    <Tooltip />
                    <Bar dataKey="val" fill={COLORS.volunteers} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className={cardClass}>
              <p className="mb-4 text-sm" style={{ color: COLORS.text }}>
                Entity signal notes
              </p>
              <div className="space-y-3 text-sm" style={{ color: COLORS.textSoft }}>
                <div className="flex items-center gap-3"><span style={{ color: COLORS.projects }}>*</span> Investor topology is now data-backed from normalized artifact fields.</div>
                <div className="flex items-center gap-3"><span style={{ color: COLORS.projects }}>*</span> Volunteer supply gaps are computed from canonical skills, not raw free text.</div>
                <div className="flex items-center gap-3"><span style={{ color: COLORS.projects }}>*</span> Funding distribution now reflects real project ask bands.</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'clusters' && (
        <div className="grid gap-6 xl:grid-cols-[1.45fr_1fr]">
          <div className="space-y-6">
            <div className={cardClass}>
              <div className="mb-4 flex items-start justify-between gap-6">
                <div>
                  <p className="mb-2 text-sm" style={{ color: COLORS.text }}>
                    Semantic landscape
                  </p>
                  <p className="max-w-2xl text-sm leading-7" style={{ color: COLORS.textSoft }}>
                    This map is for exploration, not matching. Nearby points share language, sectors, and themes, while actual recommendations are shown separately in the match network layer.
                  </p>
                </div>
                <div className="rounded-2xl border px-4 py-3 text-right" style={{ borderColor: COLORS.border, backgroundColor: COLORS.panelSoft }}>
                  <div className="text-xs uppercase tracking-[0.2em]" style={{ color: COLORS.textDim }}>
                    Semantic Nodes
                  </div>
                  <div className="mt-2 text-2xl font-light" style={{ color: COLORS.projects }}>
                    {clusters.semantic_map.length}
                  </div>
                </div>
              </div>
              <div className="h-[540px]">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart>
                    <CartesianGrid stroke={COLORS.border} strokeDasharray="3 3" />
                    <XAxis type="number" dataKey="x" name="x" stroke={COLORS.textDim} />
                    <YAxis type="number" dataKey="y" name="y" stroke={COLORS.textDim} />
                    <Tooltip
                      cursor={{ strokeDasharray: '3 3' }}
                      contentStyle={{ backgroundColor: COLORS.panel, borderColor: COLORS.border }}
                      formatter={(_, __, item) => {
                        const node = (item?.payload ?? null) as Clusters['semantic_map'][number] | null;
                        if (!node) return null;
                        return [
                          `${node.sector} | ${node.region}`,
                          `${node.name} (${node.type})`,
                        ];
                      }}
                    />
                    <Legend />
                    {semanticGroups.map((type, index) => (
                      <Scatter
                        key={type}
                        name={type}
                        data={clusters.semantic_map.filter((node) => node.type === type)}
                        fill={palette[index % palette.length]}
                      />
                    ))}
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className={cardClass}>
              <p className="mb-2 text-sm" style={{ color: COLORS.text }}>
                Match corridor scoreboard
              </p>
              <p className="mb-4 text-sm leading-7" style={{ color: COLORS.textSoft }}>
                Corridors are ranked from actual sampled fit across the four engines, not just sector overlap.
              </p>
              <div className="h-[340px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={clusters.match_corridors} layout="vertical">
                    <CartesianGrid stroke={COLORS.border} strokeDasharray="3 3" />
                    <XAxis type="number" domain={[0, 100]} stroke={COLORS.textDim} />
                    <YAxis type="category" dataKey="sector" stroke={COLORS.textSoft} width={130} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="avg_investor_score" fill={COLORS.investors} />
                    <Bar dataKey="avg_volunteer_score" fill={COLORS.volunteers} />
                    <Bar dataKey="avg_grant_score" fill={COLORS.ngos} />
                    <Bar dataKey="avg_precedent_score" fill={COLORS.teal} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className={cardClass}>
              <p className="mb-3 text-xs uppercase tracking-[0.25em]" style={{ color: COLORS.textDim }}>
                Lead Match Signal
              </p>
              <div className="mb-2 text-3xl font-light text-white">{clusters.cluster_signal.lead_sector}</div>
              <p className="mb-5 text-sm leading-7" style={{ color: COLORS.textSoft }}>
                {clusters.cluster_signal.narrative}
              </p>
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-2xl border p-4" style={{ borderColor: COLORS.border, backgroundColor: COLORS.panelSoft }}>
                  <div className="text-xs uppercase tracking-[0.2em]" style={{ color: COLORS.textDim }}>
                    Fit Index
                  </div>
                  <div className="mt-2 text-2xl font-light" style={{ color: COLORS.projects }}>
                    {clusters.cluster_signal.fit_index}
                  </div>
                </div>
                <div className="rounded-2xl border p-4" style={{ borderColor: COLORS.border, backgroundColor: COLORS.panelSoft }}>
                  <div className="text-xs uppercase tracking-[0.2em]" style={{ color: COLORS.textDim }}>
                    Match Edges
                  </div>
                  <div className="mt-2 text-2xl font-light" style={{ color: COLORS.investors }}>
                    {clusters.match_network.summary.connections}
                  </div>
                </div>
              </div>
            </div>

            <div className={cardClass}>
              <p className="mb-2 text-sm" style={{ color: COLORS.text }}>
                Actionable match network
              </p>
              <p className="mb-4 text-sm leading-7" style={{ color: COLORS.textSoft }}>
                These are actual recommendation edges from the match engines, sorted by score.
              </p>
              <div className="space-y-3">
                {matchEdgeRows.slice(0, 8).map((edge) => (
                  <div
                    key={`${edge.source}-${edge.target}`}
                    className="rounded-2xl border px-4 py-3"
                    style={{ borderColor: COLORS.border, backgroundColor: COLORS.panelSoft }}
                  >
                    <div className="mb-1 flex items-center justify-between gap-4">
                      <div className="text-sm text-white">{edge.sourceName}</div>
                      <div className="text-sm font-medium" style={{ color: COLORS.projects }}>
                        {edge.value}
                      </div>
                    </div>
                    <div className="mb-1 text-xs uppercase tracking-[0.18em]" style={{ color: COLORS.textDim }}>
                      {edge.relation}
                    </div>
                    <div className="text-sm" style={{ color: COLORS.textSoft }}>
                      {edge.targetName}
                    </div>
                    <div className="mt-2 text-xs leading-6" style={{ color: COLORS.textDim }}>
                      {edge.rationale}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className={cardClass}>
              <p className="mb-4 text-sm" style={{ color: COLORS.text }}>
                Representative project match stories
              </p>
              <div className="space-y-4">
                {clusters.project_match_panels.map((panel) => (
                  <div
                    key={panel.project_id}
                    className="rounded-2xl border p-4"
                    style={{ borderColor: COLORS.border, backgroundColor: COLORS.panelSoft }}
                  >
                    <div className="text-sm text-white">{panel.project_title}</div>
                    <div className="mb-3 mt-1 text-xs uppercase tracking-[0.18em]" style={{ color: COLORS.textDim }}>
                      {panel.sector} | {panel.stage} | {panel.country}
                    </div>
                    <div className="space-y-2 text-sm" style={{ color: COLORS.textSoft }}>
                      <div className="flex items-start justify-between gap-4">
                        <span>Investor</span>
                        <span className="text-right">{panel.investor ? `${panel.investor.name} (${panel.investor.score})` : 'No high-confidence edge'}</span>
                      </div>
                      <div className="flex items-start justify-between gap-4">
                        <span>Volunteer</span>
                        <span className="text-right">{panel.volunteer ? `${panel.volunteer.name} (${panel.volunteer.score})` : 'No high-confidence edge'}</span>
                      </div>
                      <div className="flex items-start justify-between gap-4">
                        <span>Grant</span>
                        <span className="text-right">{panel.grant ? `${panel.grant.name} (${panel.grant.score})` : 'No high-confidence edge'}</span>
                      </div>
                      <div className="flex items-start justify-between gap-4">
                        <span>Precedent</span>
                        <span className="text-right">{panel.precedent ? `${panel.precedent.name} (${panel.precedent.score})` : 'No high-confidence edge'}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'geography' && (
        <div className="grid gap-6 xl:grid-cols-[340px_1fr]">
          <div className="space-y-6">
            <div className={cardClass}>
              <div className="mb-5 flex items-start justify-between gap-4">
                <div>
                  <p className="mb-2 text-sm" style={{ color: COLORS.text }}>
                    Geographic filters
                  </p>
                  <p className="text-sm leading-7" style={{ color: COLORS.textSoft }}>
                    Every location is shown with an explicit country or IATI region label. Region-only activities stay grouped as regions until country data exists.
                  </p>
                </div>
                <Filter className="h-5 w-5" style={{ color: COLORS.projects }} />
              </div>

              <div className="mb-5">
                <div className="mb-3 text-xs uppercase tracking-[0.2em]" style={{ color: COLORS.textDim }}>
                  Layer
                </div>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(geoLayerMeta).map(([key, meta]) => (
                    <button
                      key={key}
                      onClick={() => setGeoLayer(key as keyof typeof geoLayerMeta)}
                      className="rounded-full border px-3 py-2 text-xs transition"
                      style={
                        geoLayer === key
                          ? { borderColor: meta.tone, backgroundColor: `${meta.tone}22`, color: meta.tone }
                          : { borderColor: COLORS.border, color: COLORS.textSoft }
                      }
                    >
                      {meta.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="mb-5">
                <div className="mb-2 text-xs uppercase tracking-[0.2em]" style={{ color: COLORS.textDim }}>
                  Place Type
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    ['all', 'All'],
                    ['country', 'Countries'],
                    ['region', 'Regions'],
                  ].map(([value, label]) => (
                    <button
                      key={value}
                      onClick={() => setGeoPlaceType(value as typeof geoPlaceType)}
                      className="rounded-2xl border px-3 py-3 text-sm transition"
                      style={
                        geoPlaceType === value
                          ? { borderColor: COLORS.projects, backgroundColor: 'rgba(25,194,143,0.14)', color: COLORS.text }
                          : { borderColor: COLORS.border, color: COLORS.textSoft }
                      }
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="mb-2 block text-xs uppercase tracking-[0.2em]" style={{ color: COLORS.textDim }}>
                  Sector
                </label>
                <select
                  value={geoSector}
                  onChange={(event) => setGeoSector(event.target.value)}
                  className="w-full rounded-2xl border px-4 py-3 text-sm outline-none"
                  style={{ borderColor: COLORS.border, backgroundColor: COLORS.panelSoft, color: COLORS.text }}
                >
                  <option value="All sectors">All sectors</option>
                  {geoMap.filters.sectors.map((sector) => (
                    <option key={sector} value={sector}>
                      {sector}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className={cardClass}>
              <p className="mb-4 text-sm" style={{ color: COLORS.text }}>
                Coverage snapshot
              </p>
              <div className="grid gap-3">
                {[
                  ['Tracked activities', geoMap.summary.tracked_activities, COLORS.projects],
                  ['Distinct places', geoMap.summary.distinct_places, COLORS.investors],
                  ['Mapped locations', geoMap.summary.mapped_locations, COLORS.volunteers],
                  ['Unlocated activities', geoMap.summary.unlocated_activities, COLORS.ngos],
                ].map(([label, value, tone]) => (
                  <div
                    key={String(label)}
                    className="rounded-2xl border px-4 py-3"
                    style={{ borderColor: COLORS.border, backgroundColor: COLORS.panelSoft }}
                  >
                    <div className="text-xs uppercase tracking-[0.18em]" style={{ color: COLORS.textDim }}>
                      {label}
                    </div>
                    <div className="mt-2 text-2xl font-light" style={{ color: String(tone) }}>
                      {value}
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-5 rounded-2xl border p-4" style={{ borderColor: COLORS.border, backgroundColor: COLORS.panelSoft }}>
                <div className="text-xs uppercase tracking-[0.18em]" style={{ color: COLORS.textDim }}>
                  Top activity hotspot
                </div>
                <div className="mt-2 text-lg text-white">{geoMap.summary.top_activity_location.name}</div>
                <div className="mt-1 text-sm" style={{ color: COLORS.textSoft }}>
                  {geoMap.summary.top_activity_location.count} activities in the current dataset.
                </div>
              </div>
            </div>

            <div className={cardClass}>
              <div className="mb-4 flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm" style={{ color: COLORS.text }}>
                    Selected location
                  </p>
                  <p className="mt-1 text-sm" style={{ color: COLORS.textSoft }}>
                    Click a bubble or hotspot row to inspect local density.
                  </p>
                </div>
                <MapPinned className="h-5 w-5" style={{ color: COLORS.projects }} />
              </div>

              {activeGeoPoint ? (
                <div className="space-y-4">
                  <div>
                    <div className="text-xl text-white">{activeGeoPoint.name}</div>
                    <div className="mt-1 text-xs uppercase tracking-[0.18em]" style={{ color: COLORS.textDim }}>
                      {activeGeoPoint.place_type === 'country' ? 'Country' : 'Regional Program'} | {geoLayerMeta[geoLayer].label}:{' '}
                      {geoMetricValue(activeGeoPoint, geoLayer)}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    {[
                      ['Activities', activeGeoPoint.activity_count, COLORS.projects],
                      ['Projects', activeGeoPoint.project_count, COLORS.investors],
                      ['Volunteers', activeGeoPoint.volunteer_count, COLORS.volunteers],
                      ['Investors', activeGeoPoint.investor_count, COLORS.ngos],
                    ].map(([label, value, tone]) => (
                      <div
                        key={String(label)}
                        className="rounded-2xl border p-3"
                        style={{ borderColor: COLORS.border, backgroundColor: COLORS.panelSoft }}
                      >
                        <div className="text-xs uppercase tracking-[0.18em]" style={{ color: COLORS.textDim }}>
                          {label}
                        </div>
                        <div className="mt-2 text-xl font-light" style={{ color: String(tone) }}>
                          {value}
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="rounded-2xl border p-4" style={{ borderColor: COLORS.border, backgroundColor: COLORS.panelSoft }}>
                    <div className="mb-2 text-xs uppercase tracking-[0.18em]" style={{ color: COLORS.textDim }}>
                      Dominant activity sector
                    </div>
                    <div className="text-sm text-white">{activeGeoPoint.dominant_sector}</div>
                    <div className="mt-3 space-y-2">
                      {activeGeoPoint.sector_breakdown.slice(0, 4).map((sector) => (
                        <div key={sector.name} className="flex items-center gap-3">
                          <div className="w-24 text-xs" style={{ color: COLORS.textSoft }}>
                            {sector.name}
                          </div>
                          <div className="h-2 flex-1 rounded-full bg-[#1a2b45]">
                            <div
                              className="h-2 rounded-full"
                              style={{
                                width: `${Math.max(8, (sector.value / Math.max(activeGeoPoint.activity_count, 1)) * 100)}%`,
                                backgroundColor: COLORS.projects,
                              }}
                            />
                          </div>
                          <div className="w-8 text-right text-xs" style={{ color: COLORS.text }}>
                            {sector.value}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-2xl border p-4" style={{ borderColor: COLORS.border, backgroundColor: COLORS.panelSoft }}>
                    <div className="mb-2 text-xs uppercase tracking-[0.18em]" style={{ color: COLORS.textDim }}>
                      Sample organizations
                    </div>
                    <div className="space-y-2 text-sm" style={{ color: COLORS.textSoft }}>
                      {activeGeoPoint.sample_organizations.length ? (
                        activeGeoPoint.sample_organizations.map((organization) => <div key={organization}>{organization}</div>)
                      ) : (
                        <div>No organization samples available for this location.</div>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-sm" style={{ color: COLORS.textSoft }}>
                  No locations match the current filter set.
                </div>
              )}
            </div>
          </div>

          <div className="space-y-6">
            <div className={cardClass}>
              <div className="mb-5 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                <div>
                  <p className="mb-2 text-sm" style={{ color: COLORS.text }}>
                    Activity intensity map
                  </p>
                  <p className="max-w-3xl text-sm leading-7" style={{ color: COLORS.textSoft }}>
                    Bubble size tracks the selected layer. Countries use explicit country names, while cross-border programs without country-level precision stay mapped as regional hubs.
                  </p>
                </div>
                <div className="rounded-2xl border px-4 py-3 text-right" style={{ borderColor: COLORS.border, backgroundColor: COLORS.panelSoft }}>
                  <div className="text-xs uppercase tracking-[0.18em]" style={{ color: COLORS.textDim }}>
                    Filtered locations
                  </div>
                  <div className="mt-2 text-2xl font-light" style={{ color: geoLayerMeta[geoLayer].tone }}>
                    {filteredGeoPoints.length}
                  </div>
                </div>
              </div>

              <div
                className="relative overflow-hidden rounded-[28px] border"
                style={{
                  borderColor: COLORS.border,
                  background:
                    'radial-gradient(circle at 20% 18%, rgba(79,124,255,0.18), transparent 18%), radial-gradient(circle at 80% 16%, rgba(25,194,143,0.12), transparent 22%), linear-gradient(180deg, rgba(9,18,30,0.96), rgba(12,23,38,0.96))',
                }}
              >
                <svg viewBox={`0 0 ${geoBounds.width} ${geoBounds.height}`} className="h-[560px] w-full">
                  {[-120, -60, 0, 60, 120].map((longitude) => {
                    const x = ((longitude + 180) / 360) * geoBounds.width;
                    return (
                      <line
                        key={longitude}
                        x1={x}
                        y1={0}
                        x2={x}
                        y2={geoBounds.height}
                        stroke="rgba(111,130,156,0.20)"
                        strokeDasharray="4 10"
                      />
                    );
                  })}
                  {[-30, 0, 30, 60].map((latitude) => {
                    const y = ((geoBounds.maxLat - latitude) / (geoBounds.maxLat - geoBounds.minLat)) * geoBounds.height;
                    return (
                      <line
                        key={latitude}
                        x1={0}
                        y1={y}
                        x2={geoBounds.width}
                        y2={y}
                        stroke="rgba(111,130,156,0.20)"
                        strokeDasharray="4 10"
                      />
                    );
                  })}

                  {[
                    ['North America', 170, 150],
                    ['South America', 260, 360],
                    ['Europe', 505, 110],
                    ['Africa', 520, 260],
                    ['Middle East', 615, 210],
                    ['Asia', 740, 190],
                    ['Oceania', 865, 365],
                  ].map(([label, x, y]) => (
                    <text
                      key={String(label)}
                      x={Number(x)}
                      y={Number(y)}
                      fill="rgba(159,176,199,0.45)"
                      fontSize="18"
                      letterSpacing="2"
                      textAnchor="middle"
                    >
                      {label}
                    </text>
                  ))}

                  {[...mappedGeoPoints]
                    .sort((left, right) => geoMetricValue(left, geoLayer) - geoMetricValue(right, geoLayer))
                    .map((point) => {
                      const { x, y } = projectGeoPoint(point.lat ?? 0, point.lon ?? 0);
                      const metric = geoMetricValue(point, geoLayer);
                      const radius = 7 + Math.sqrt(metric / maxGeoMetric) * 26;
                      const selected = activeGeoPoint?.id === point.id;
                      const showLabel = topGeoLabelIds.includes(point.id);

                      return (
                        <g key={point.id} onClick={() => setSelectedGeoId(point.id)} style={{ cursor: 'pointer' }}>
                          <circle
                            cx={x}
                            cy={y}
                            r={radius}
                            fill={selected ? COLORS.text : geoLayerMeta[geoLayer].tone}
                            fillOpacity={selected ? 0.96 : 0.74}
                            stroke={selected ? geoLayerMeta[geoLayer].tone : 'rgba(236,242,248,0.18)'}
                            strokeWidth={selected ? 3 : 1.5}
                          />
                          <circle
                            cx={x}
                            cy={y}
                            r={radius + 6}
                            fill="none"
                            stroke={selected ? 'rgba(236,242,248,0.42)' : 'rgba(236,242,248,0.06)'}
                            strokeWidth={1}
                          />
                          {showLabel && (
                            <text
                              x={x}
                              y={Math.max(18, y - radius - 10)}
                              fill={selected ? COLORS.text : COLORS.textSoft}
                              fontSize="13"
                              textAnchor="middle"
                            >
                              {point.name}
                            </text>
                          )}
                        </g>
                      );
                    })}
                </svg>

                <div className="pointer-events-none absolute left-4 top-4 rounded-2xl border px-4 py-3" style={{ borderColor: COLORS.border, backgroundColor: 'rgba(8,17,31,0.84)' }}>
                  <div className="text-xs uppercase tracking-[0.18em]" style={{ color: COLORS.textDim }}>
                    Active layer
                  </div>
                  <div className="mt-2 text-lg" style={{ color: geoLayerMeta[geoLayer].tone }}>
                    {geoLayerMeta[geoLayer].label}
                  </div>
                </div>
              </div>
            </div>

            <div className={cardClass}>
              <div className="mb-4 flex items-start justify-between gap-4">
                <div>
                  <p className="mb-2 text-sm" style={{ color: COLORS.text }}>
                    Hotspot ranking
                  </p>
                  <p className="text-sm leading-7" style={{ color: COLORS.textSoft }}>
                    Ranked by the selected layer so we can immediately see where activity, projects, volunteers, or investors are densest.
                  </p>
                </div>
                <Building2 className="h-5 w-5" style={{ color: COLORS.projects }} />
              </div>

              <div className="space-y-3">
                {filteredGeoPoints.slice(0, 10).map((point) => {
                  const selected = activeGeoPoint?.id === point.id;
                  return (
                    <button
                      key={point.id}
                      onClick={() => setSelectedGeoId(point.id)}
                      className="flex w-full items-center justify-between gap-4 rounded-2xl border px-4 py-3 text-left transition"
                      style={
                        selected
                          ? { borderColor: COLORS.projects, backgroundColor: 'rgba(25,194,143,0.10)' }
                          : { borderColor: COLORS.border, backgroundColor: COLORS.panelSoft }
                      }
                    >
                      <div>
                        <div className="text-sm text-white">{point.name}</div>
                        <div className="mt-1 text-xs uppercase tracking-[0.16em]" style={{ color: COLORS.textDim }}>
                          {point.place_type === 'country' ? 'Country' : 'Regional Program'} | {point.dominant_sector}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-light" style={{ color: geoLayerMeta[geoLayer].tone }}>
                          {geoMetricValue(point, geoLayer)}
                        </div>
                        <div className="text-xs" style={{ color: COLORS.textSoft }}>
                          activities: {point.activity_count}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
