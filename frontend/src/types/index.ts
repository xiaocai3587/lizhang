// 类型定义

// 人物分组
export type PersonGroup = 'my_family' | 'wife_family' | 'friends';

// 性别（后端返回自由字符串，可能是 "male"/"female"/"男"/"女"/""）
export type Gender = string;

// 人物
export interface Person {
  id: string;
  name: string;
  nickname: string;
  group: PersonGroup;
  gender: Gender;
  birth_year: string;
  is_self: boolean;
  title: string;
  gift_status: GiftStatus;
  notes: string;
  created_at: string;
}

export type GiftStatus = 'normal' | 'excluded';

export interface PersonCreate {
  name: string;
  nickname?: string;
  group: PersonGroup;
  gender?: Gender;
  birth_year?: string;
  is_self?: boolean;
  title?: string;
  gift_status?: GiftStatus;
  notes?: string;
}

export interface PersonUpdate {
  name?: string;
  nickname?: string;
  group?: PersonGroup;
  gender?: Gender;
  birth_year?: string;
  is_self?: boolean;
  title?: string;
  gift_status?: GiftStatus;
  notes?: string;
}

// 人物统计
export interface PersonStats {
  total_gave: number;
  total_received: number;
  net: number;
  gift_count: number;
}

// 事件角色
export type EventRole = 'received' | 'given';

// 事件
export interface GiftEvent {
  id: string;
  title: string;
  event_type: string;
  date: string;
  role: EventRole;
  notes: string;
  gift_count: number;
  gift_total: number;
}

export interface EventCreate {
  title: string;
  event_type?: string;
  date: string;
  role: EventRole;
  notes?: string;
}

export interface EventUpdate {
  title?: string;
  event_type?: string;
  date?: string;
  role?: EventRole;
  notes?: string;
}

// 礼金参与者
export type ParticipantRole = 'giver' | 'receiver';

export interface Participant {
  person_id: string;
  person_name?: string;
  role: ParticipantRole;
}

// 礼金
export interface Gift {
  id: string;
  event_id: string;
  amount: number;
  is_shared: boolean;
  notes: string;
  participants: Participant[];
}

export interface GiftCreate {
  event_id: string;
  amount: number;
  is_shared?: boolean;
  notes?: string;
  participants: { person_id: string; role: ParticipantRole }[];
}

export interface GiftUpdate {
  event_id?: string;
  amount?: number;
  is_shared?: boolean;
  notes?: string;
  participants?: { person_id: string; role: ParticipantRole }[];
}

// 关系
export type RelationType = 'parent_child' | 'spouse' | 'sibling';

export interface Relation {
  id: string;
  from_id: string;
  to_id: string;
  type: RelationType;
  notes: string;
  from_name?: string;
  to_name?: string;
}

export interface RelationCreate {
  from_id: string;
  to_id: string;
  type: RelationType;
  notes?: string;
}

// 图谱节点/边
export interface GraphNode {
  id: string;
  name: string;
  gender: Gender;
  group: PersonGroup;
  is_self: boolean;
  birth_year: string;
  depth: number;
  total_amount?: number;
}

export interface GraphLink {
  source: string;
  target: string;
  type: 'parent_child' | 'spouse' | 'sibling' | 'friend' | 'gift';
  amount?: number;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

// 家庭单元族谱（夫妻对节点）
export interface HouseholdMember {
  id: string;
  name: string;
  nickname: string;
  gender: Gender;
  group: PersonGroup;
  is_self: boolean;
  birth_year: string;
  title: string; // 称谓（优先手动title，否则自动推算）
}

export interface HouseholdNode {
  id: string; // household id, 如 "h_xxx_yyy"
  members: HouseholdMember[]; // 1或2人
  depth: number; // 0=锚点, 负=祖先, 正=后代
  is_anchor: boolean;
  side: 'paternal' | 'maternal' | 'self'; // 父系左 / 母系右 / 中间
}

export interface HouseholdGraphData {
  nodes: HouseholdNode[];
  links: GraphLink[];
}

// 仪表盘统计
export interface RecentEvent {
  id: string;
  title: string;
  date: string;
  event_type: string;
  role: EventRole;
  gift_count: number;
  gift_total: number;
}

export interface TopPerson {
  person_id: string;
  name: string;
  total_amount: number;
}

export interface MonthlyTrend {
  month: string;
  received: number;
  given: number;
}

export interface DashboardStats {
  persons_count: number;
  events_count: number;
  gifts_count: number;
  total_received: number;
  total_given: number;
  net: number;
  recent_events: RecentEvent[];
  top_persons: TopPerson[];
  monthly_trend: MonthlyTrend[];
}

// 回礼建议
export interface Suggestion {
  person_id: string;
  person_name: string;
  suggested_amount: number;
  last_gift_amount: number | null;
  last_gift_date: string | null;
  reason: string;
}
