import React, { useState, useCallback } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, FlatList, ActivityIndicator, RefreshControl } from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../../src/api';
import { colors, spacing, radius } from '../../src/theme';

const c = colors.light;
const FILTERS = ['all', 'scheduled', 'confirmed', 'completed', 'cancelled'];

export default function AppointmentsScreen() {
  const router = useRouter();
  const [appointments, setAppointments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState('all');

  const loadData = useCallback(async () => {
    try {
      const params = filter !== 'all' ? `status=${filter}` : '';
      const data = await api.getAppointments(params);
      setAppointments(data);
    } catch (e) {
      console.log('Appointments load error:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [filter]);

  useFocusEffect(useCallback(() => { loadData(); }, [loadData]));

  function getStatusColor(status: string) {
    switch (status) {
      case 'confirmed': return c.success;
      case 'scheduled': return c.warning;
      case 'completed': return c.primary;
      case 'cancelled': return c.accent;
      default: return c.textMuted;
    }
  }

  const renderItem = ({ item }: any) => (
    <TouchableOpacity
      testID={`appointment-item-${item.id}`}
      style={styles.card}
      onPress={() => router.push({ pathname: '/appointment-detail', params: { id: item.id } })}
      activeOpacity={0.7}
    >
      <View style={styles.cardTop}>
        <View style={styles.cardLeft}>
          <View style={[styles.statusDot, { backgroundColor: getStatusColor(item.status) }]} />
          <View>
            <Text style={styles.patientName}>{item.patient_name}</Text>
            <Text style={styles.problem}>{item.problem_description || 'General'}</Text>
          </View>
        </View>
        <Ionicons name="chevron-forward" size={20} color={c.textMuted} />
      </View>
      <View style={styles.cardBottom}>
        <View style={styles.infoChip}>
          <Ionicons name="calendar-outline" size={14} color={c.textMuted} />
          <Text style={styles.infoText}>{item.preferred_date}</Text>
        </View>
        <View style={styles.infoChip}>
          <Ionicons name="time-outline" size={14} color={c.textMuted} />
          <Text style={styles.infoText}>{item.preferred_time}</Text>
        </View>
        <View style={[styles.statusChip, { backgroundColor: getStatusColor(item.status) + '15' }]}>
          <Text style={[styles.statusChipText, { color: getStatusColor(item.status) }]}>{item.status}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.header}>
        <Text style={styles.title}>Appointments</Text>
        <TouchableOpacity testID="add-appointment-btn" style={styles.addBtn} onPress={() => router.push('/add-appointment')}>
          <Ionicons name="add" size={24} color="#FFF" />
        </TouchableOpacity>
      </View>

      {/* Filters */}
      <FlatList
        horizontal
        data={FILTERS}
        keyExtractor={(item) => item}
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.filterRow}
        renderItem={({ item }) => (
          <TouchableOpacity
            testID={`filter-${item}`}
            style={[styles.filterChip, filter === item && styles.filterChipActive]}
            onPress={() => setFilter(item)}
          >
            <Text style={[styles.filterText, filter === item && styles.filterTextActive]}>
              {item.charAt(0).toUpperCase() + item.slice(1)}
            </Text>
          </TouchableOpacity>
        )}
      />

      {loading ? (
        <View style={styles.loadingView}><ActivityIndicator size="large" color={c.primary} /></View>
      ) : (
        <FlatList
          data={appointments}
          keyExtractor={(item) => item.id}
          renderItem={renderItem}
          contentContainerStyle={styles.list}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); loadData(); }} tintColor={c.primary} />}
          ListEmptyComponent={
            <View style={styles.empty}>
              <Ionicons name="calendar-outline" size={48} color={c.textMuted} />
              <Text style={styles.emptyText}>No appointments found</Text>
            </View>
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: c.background },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: spacing.xl, paddingTop: spacing.lg, paddingBottom: spacing.md },
  title: { fontSize: 28, fontWeight: '700', color: c.textMain },
  addBtn: { width: 44, height: 44, borderRadius: 22, backgroundColor: c.primary, alignItems: 'center', justifyContent: 'center' },
  filterRow: { paddingHorizontal: spacing.xl, paddingBottom: spacing.lg, gap: spacing.sm },
  filterChip: { paddingHorizontal: spacing.lg, paddingVertical: spacing.sm, borderRadius: radius.full, backgroundColor: c.surface, borderWidth: 1, borderColor: c.border },
  filterChipActive: { backgroundColor: c.primary, borderColor: c.primary },
  filterText: { fontSize: 14, color: c.textMuted, fontWeight: '500' },
  filterTextActive: { color: '#FFF' },
  loadingView: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  list: { paddingHorizontal: spacing.xl, paddingBottom: 100 },
  card: { backgroundColor: c.surface, borderRadius: radius.lg, padding: spacing.lg, marginBottom: spacing.md, borderWidth: 1, borderColor: c.border },
  cardTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.md },
  cardLeft: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  statusDot: { width: 10, height: 10, borderRadius: 5, marginRight: spacing.md },
  patientName: { fontSize: 16, fontWeight: '600', color: c.textMain },
  problem: { fontSize: 13, color: c.textMuted, marginTop: 2 },
  cardBottom: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  infoChip: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  infoText: { fontSize: 13, color: c.textMuted },
  statusChip: { borderRadius: radius.full, paddingHorizontal: spacing.md, paddingVertical: 2, marginLeft: 'auto' },
  statusChipText: { fontSize: 12, fontWeight: '600', textTransform: 'capitalize' },
  empty: { alignItems: 'center', paddingTop: spacing.xxxl },
  emptyText: { fontSize: 16, color: c.textMuted, marginTop: spacing.lg },
});
