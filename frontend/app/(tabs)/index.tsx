import React, { useState, useCallback } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, ActivityIndicator, RefreshControl } from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../src/auth';
import { api } from '../../src/api';
import { colors, spacing, radius } from '../../src/theme';

const c = colors.light;

export default function DashboardScreen() {
  const router = useRouter();
  const { user } = useAuth();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [aiToggling, setAiToggling] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const data = await api.getDashboardStats();
      setStats(data);
    } catch (e) {
      console.log('Dashboard load error:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { loadData(); }, [loadData]));

  async function toggleAI() {
    setAiToggling(true);
    try {
      const res = await api.toggleAIAgent();
      setStats((prev: any) => prev ? { ...prev, ai_agent_active: res.is_active } : prev);
    } catch (e) {
      console.log('Toggle AI error:', e);
    } finally {
      setAiToggling(false);
    }
  }

  if (loading) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.loadingView}><ActivityIndicator size="large" color={c.primary} /></View>
      </SafeAreaView>
    );
  }

  const aiActive = stats?.ai_agent_active || false;

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); loadData(); }} tintColor={c.primary} />}
      >
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>Good {getTimeOfDay()}</Text>
            <Text style={styles.userName}>{user?.name || 'Doctor'}</Text>
          </View>
          <TouchableOpacity testID="notifications-btn" style={styles.notifBtn}>
            <Ionicons name="notifications-outline" size={24} color={c.textMain} />
          </TouchableOpacity>
        </View>

        {/* AI Agent Card */}
        <TouchableOpacity testID="ai-agent-toggle-card" style={[styles.aiCard, aiActive && styles.aiCardActive]} onPress={toggleAI} disabled={aiToggling} activeOpacity={0.85}>
          <View style={styles.aiCardContent}>
            <View style={styles.aiIconWrap}>
              <View style={[styles.aiDot, aiActive && styles.aiDotActive]} />
              <Ionicons name="pulse" size={28} color={aiActive ? '#FFF' : c.textMuted} />
            </View>
            <View style={styles.aiTextWrap}>
              <Text style={[styles.aiTitle, aiActive && styles.aiTitleActive]}>AI Receptionist</Text>
              <Text style={[styles.aiStatus, aiActive && styles.aiStatusActive]}>
                {aiToggling ? 'Switching...' : aiActive ? 'Active - Receiving Calls' : 'Inactive - Tap to Activate'}
              </Text>
            </View>
            <View style={[styles.aiToggle, aiActive && styles.aiToggleActive]}>
              <View style={[styles.aiToggleDot, aiActive && styles.aiToggleDotActive]} />
            </View>
          </View>
        </TouchableOpacity>

        {/* Quick Stats */}
        <View style={styles.statsGrid}>
          <StatCard testID="stat-today" icon="calendar" label="Today" value={stats?.today_appointments || 0} color={c.primary} />
          <StatCard testID="stat-pending" icon="time" label="Pending" value={stats?.pending_appointments || 0} color={c.warning} />
          <StatCard testID="stat-confirmed" icon="checkmark-circle" label="Confirmed" value={stats?.confirmed_appointments || 0} color={c.success} />
          <StatCard testID="stat-patients" icon="people" label="Patients" value={stats?.total_patients || 0} color="#6366F1" />
        </View>

        {/* Quick Actions */}
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.actionsRow}>
          <ActionButton testID="action-new-appointment" icon="add-circle" label="New Appt" onPress={() => router.push('/add-appointment')} />
          <ActionButton testID="action-patients" icon="people" label="Patients" onPress={() => router.push('/patients')} />
          <ActionButton testID="action-clinic-hours" icon="time" label="Hours" onPress={() => router.push('/clinic-hours')} />
          <ActionButton testID="action-ai-config" icon="settings" label="AI Config" onPress={() => router.push('/ai-config')} />
        </View>

        {/* Today's Appointments */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Today's Appointments</Text>
          <TouchableOpacity testID="view-all-appointments-btn" onPress={() => router.push('/(tabs)/appointments')}>
            <Text style={styles.viewAll}>View All</Text>
          </TouchableOpacity>
        </View>

        {stats?.todays_appointments?.length > 0 ? (
          stats.todays_appointments.slice(0, 5).map((appt: any) => (
            <TouchableOpacity
              key={appt.id}
              testID={`appointment-card-${appt.id}`}
              style={styles.apptCard}
              onPress={() => router.push({ pathname: '/appointment-detail', params: { id: appt.id } })}
              activeOpacity={0.7}
            >
              <View style={styles.apptTime}>
                <Text style={styles.apptTimeText}>{appt.preferred_time}</Text>
              </View>
              <View style={styles.apptInfo}>
                <Text style={styles.apptName}>{appt.patient_name}</Text>
                <Text style={styles.apptProblem}>{appt.problem_description}</Text>
              </View>
              <View style={[styles.statusBadge, { backgroundColor: getStatusColor(appt.status) + '20' }]}>
                <Text style={[styles.statusText, { color: getStatusColor(appt.status) }]}>{appt.status}</Text>
              </View>
            </TouchableOpacity>
          ))
        ) : (
          <View style={styles.emptyCard}>
            <Ionicons name="calendar-outline" size={40} color={c.textMuted} />
            <Text style={styles.emptyText}>No appointments today</Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function StatCard({ testID, icon, label, value, color }: any) {
  return (
    <View testID={testID} style={styles.statCard}>
      <View style={[styles.statIcon, { backgroundColor: color + '15' }]}>
        <Ionicons name={icon} size={22} color={color} />
      </View>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

function ActionButton({ testID, icon, label, onPress }: any) {
  return (
    <TouchableOpacity testID={testID} style={styles.actionBtn} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.actionIcon}>
        <Ionicons name={icon} size={24} color={c.primary} />
      </View>
      <Text style={styles.actionLabel}>{label}</Text>
    </TouchableOpacity>
  );
}

function getTimeOfDay() {
  const h = new Date().getHours();
  if (h < 12) return 'Morning';
  if (h < 17) return 'Afternoon';
  return 'Evening';
}

function getStatusColor(status: string) {
  switch (status) {
    case 'confirmed': return c.success;
    case 'scheduled': return c.warning;
    case 'completed': return c.primary;
    case 'cancelled': return c.accent;
    default: return c.textMuted;
  }
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: c.background },
  loadingView: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  scroll: { paddingHorizontal: spacing.xl, paddingBottom: 100 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingTop: spacing.lg, paddingBottom: spacing.xl },
  greeting: { fontSize: 14, color: c.textMuted },
  userName: { fontSize: 24, fontWeight: '700', color: c.textMain, marginTop: 2 },
  notifBtn: { width: 44, height: 44, borderRadius: 22, backgroundColor: c.surface, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: c.border },

  // AI Card
  aiCard: { backgroundColor: c.surface, borderRadius: radius.lg, padding: spacing.xl, marginBottom: spacing.xl, borderWidth: 1, borderColor: c.border, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.04, shadowRadius: 8, elevation: 2 },
  aiCardActive: { backgroundColor: '#7C3AED', borderColor: '#7C3AED' },
  aiCardContent: { flexDirection: 'row', alignItems: 'center' },
  aiIconWrap: { flexDirection: 'row', alignItems: 'center', marginRight: spacing.lg },
  aiDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: c.textMuted, marginRight: spacing.sm },
  aiDotActive: { backgroundColor: '#34D399' },
  aiTextWrap: { flex: 1 },
  aiTitle: { fontSize: 18, fontWeight: '600', color: c.textMain },
  aiTitleActive: { color: '#FFF' },
  aiStatus: { fontSize: 13, color: c.textMuted, marginTop: 2 },
  aiStatusActive: { color: 'rgba(255,255,255,0.8)' },
  aiToggle: { width: 52, height: 30, borderRadius: 15, backgroundColor: c.border, justifyContent: 'center', paddingHorizontal: 3 },
  aiToggleActive: { backgroundColor: '#34D399' },
  aiToggleDot: { width: 24, height: 24, borderRadius: 12, backgroundColor: '#FFF' },
  aiToggleDotActive: { alignSelf: 'flex-end' },

  // Stats
  statsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md, marginBottom: spacing.xl },
  statCard: { width: '48%', flexGrow: 1, backgroundColor: c.surface, borderRadius: radius.lg, padding: spacing.lg, borderWidth: 1, borderColor: c.border },
  statIcon: { width: 40, height: 40, borderRadius: radius.md, alignItems: 'center', justifyContent: 'center', marginBottom: spacing.sm },
  statValue: { fontSize: 28, fontWeight: '700', color: c.textMain },
  statLabel: { fontSize: 13, color: c.textMuted, marginTop: 2 },

  // Actions
  actionsRow: { flexDirection: 'row', gap: spacing.md, marginBottom: spacing.xxl },
  actionBtn: { flex: 1, alignItems: 'center', backgroundColor: c.surface, borderRadius: radius.lg, paddingVertical: spacing.lg, borderWidth: 1, borderColor: c.border },
  actionIcon: { width: 44, height: 44, borderRadius: 22, backgroundColor: c.secondary, alignItems: 'center', justifyContent: 'center', marginBottom: spacing.sm },
  actionLabel: { fontSize: 12, fontWeight: '500', color: c.textMain },

  // Section
  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.lg },
  sectionTitle: { fontSize: 18, fontWeight: '600', color: c.textMain, marginBottom: spacing.lg },
  viewAll: { fontSize: 14, color: c.primary, fontWeight: '500' },

  // Appointment Card
  apptCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: c.surface, borderRadius: radius.md, padding: spacing.lg, marginBottom: spacing.md, borderWidth: 1, borderColor: c.border },
  apptTime: { backgroundColor: c.secondary, borderRadius: radius.sm, paddingHorizontal: spacing.md, paddingVertical: spacing.sm, marginRight: spacing.lg },
  apptTimeText: { fontSize: 14, fontWeight: '600', color: c.primary },
  apptInfo: { flex: 1 },
  apptName: { fontSize: 16, fontWeight: '600', color: c.textMain },
  apptProblem: { fontSize: 13, color: c.textMuted, marginTop: 2 },
  statusBadge: { borderRadius: radius.full, paddingHorizontal: spacing.md, paddingVertical: spacing.xs },
  statusText: { fontSize: 11, fontWeight: '600', textTransform: 'capitalize' },

  // Empty
  emptyCard: { alignItems: 'center', paddingVertical: spacing.xxxl, backgroundColor: c.surface, borderRadius: radius.lg, borderWidth: 1, borderColor: c.border },
  emptyText: { fontSize: 14, color: c.textMuted, marginTop: spacing.md },
});
