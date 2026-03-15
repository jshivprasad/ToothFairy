import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, ActivityIndicator, FlatList } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../src/api';
import { colors, spacing, radius } from '../src/theme';

const c = colors.light;
const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

export default function CalendarScreen() {
  const router = useRouter();
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [appointmentsByDate, setAppointmentsByDate] = useState<Record<string, any[]>>({});
  const [selectedDate, setSelectedDate] = useState(now.toISOString().split('T')[0]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadCalendar(); }, [month, year]);

  async function loadCalendar() {
    setLoading(true);
    try {
      const data = await api.getCalendarAppointments(month, year);
      setAppointmentsByDate(data.appointments_by_date || {});
    } catch (e) {
      console.log('Calendar error:', e);
    } finally {
      setLoading(false);
    }
  }

  function prevMonth() {
    if (month === 1) { setMonth(12); setYear(year - 1); }
    else setMonth(month - 1);
  }

  function nextMonth() {
    if (month === 12) { setMonth(1); setYear(year + 1); }
    else setMonth(month + 1);
  }

  // Build calendar grid
  const firstDay = new Date(year, month - 1, 1).getDay();
  const daysInMonth = new Date(year, month, 0).getDate();
  const cells = [];
  for (let i = 0; i < firstDay; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);

  const selectedAppts = appointmentsByDate[selectedDate] || [];

  function getStatusColor(status: string) {
    switch (status) {
      case 'confirmed': return c.success;
      case 'scheduled': return c.warning;
      case 'completed': return c.primary;
      case 'cancelled': return c.accent;
      default: return c.textMuted;
    }
  }

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        {/* Month Nav */}
        <View style={styles.monthNav}>
          <TouchableOpacity testID="prev-month-btn" onPress={prevMonth} style={styles.navBtn}>
            <Ionicons name="chevron-back" size={24} color={c.textMain} />
          </TouchableOpacity>
          <Text style={styles.monthText}>{MONTHS[month - 1]} {year}</Text>
          <TouchableOpacity testID="next-month-btn" onPress={nextMonth} style={styles.navBtn}>
            <Ionicons name="chevron-forward" size={24} color={c.textMain} />
          </TouchableOpacity>
        </View>

        {/* Day Headers */}
        <View style={styles.dayHeaders}>
          {DAYS.map(d => (
            <Text key={d} style={styles.dayHeaderText}>{d}</Text>
          ))}
        </View>

        {/* Calendar Grid */}
        {loading ? (
          <ActivityIndicator size="large" color={c.primary} style={{ padding: 40 }} />
        ) : (
          <View style={styles.grid}>
            {cells.map((day, i) => {
              if (day === null) return <View key={`e-${i}`} style={styles.cell} />;
              const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
              const hasAppts = appointmentsByDate[dateStr]?.length > 0;
              const isSelected = dateStr === selectedDate;
              const isToday = dateStr === now.toISOString().split('T')[0];

              return (
                <TouchableOpacity
                  key={day}
                  testID={`cal-day-${day}`}
                  style={[styles.cell, isSelected && styles.cellSelected, isToday && !isSelected && styles.cellToday]}
                  onPress={() => setSelectedDate(dateStr)}
                >
                  <Text style={[styles.cellText, isSelected && styles.cellTextSelected, isToday && !isSelected && styles.cellTextToday]}>{day}</Text>
                  {hasAppts && (
                    <View style={[styles.dot, isSelected && styles.dotSelected]} />
                  )}
                </TouchableOpacity>
              );
            })}
          </View>
        )}

        {/* Selected Date Appointments */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            {selectedDate === now.toISOString().split('T')[0] ? 'Today' : selectedDate}
            {selectedAppts.length > 0 ? ` — ${selectedAppts.length} appointment${selectedAppts.length > 1 ? 's' : ''}` : ''}
          </Text>

          {selectedAppts.length > 0 ? (
            selectedAppts.map((appt) => (
              <TouchableOpacity
                key={appt.id}
                testID={`cal-appt-${appt.id}`}
                style={styles.apptCard}
                onPress={() => router.push({ pathname: '/appointment-detail', params: { id: appt.id } })}
              >
                <View style={[styles.timeBadge, { backgroundColor: getStatusColor(appt.status) + '15' }]}>
                  <Text style={[styles.timeText, { color: getStatusColor(appt.status) }]}>{appt.preferred_time}</Text>
                </View>
                <View style={styles.apptInfo}>
                  <Text style={styles.apptName}>{appt.patient_name}</Text>
                  <Text style={styles.apptProblem}>{appt.problem_description}</Text>
                </View>
                <View style={[styles.statusChip, { backgroundColor: getStatusColor(appt.status) + '15' }]}>
                  <Text style={[styles.statusText, { color: getStatusColor(appt.status) }]}>{appt.status}</Text>
                </View>
              </TouchableOpacity>
            ))
          ) : (
            <View style={styles.emptyCard}>
              <Ionicons name="calendar-outline" size={32} color={c.textMuted} />
              <Text style={styles.emptyText}>No appointments</Text>
            </View>
          )}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: c.background },
  scroll: { padding: spacing.xl, paddingBottom: 100 },
  monthNav: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.xl },
  navBtn: { width: 44, height: 44, borderRadius: 22, backgroundColor: c.surface, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: c.border },
  monthText: { fontSize: 20, fontWeight: '600', color: c.textMain },
  dayHeaders: { flexDirection: 'row', marginBottom: spacing.sm },
  dayHeaderText: { flex: 1, textAlign: 'center', fontSize: 13, fontWeight: '600', color: c.textMuted },
  grid: { flexDirection: 'row', flexWrap: 'wrap' },
  cell: { width: `${100 / 7}%`, aspectRatio: 1, alignItems: 'center', justifyContent: 'center' },
  cellSelected: { backgroundColor: c.primary, borderRadius: radius.full },
  cellToday: { borderWidth: 2, borderColor: c.primary, borderRadius: radius.full },
  cellText: { fontSize: 16, color: c.textMain },
  cellTextSelected: { color: '#FFF', fontWeight: '600' },
  cellTextToday: { color: c.primary, fontWeight: '600' },
  dot: { width: 5, height: 5, borderRadius: 3, backgroundColor: c.primary, marginTop: 2 },
  dotSelected: { backgroundColor: '#FFF' },
  section: { marginTop: spacing.xxl },
  sectionTitle: { fontSize: 16, fontWeight: '600', color: c.textMain, marginBottom: spacing.lg },
  apptCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: c.surface, borderRadius: radius.md, padding: spacing.lg, marginBottom: spacing.md, borderWidth: 1, borderColor: c.border },
  timeBadge: { borderRadius: radius.sm, paddingHorizontal: spacing.md, paddingVertical: spacing.sm, marginRight: spacing.md },
  timeText: { fontSize: 14, fontWeight: '600' },
  apptInfo: { flex: 1 },
  apptName: { fontSize: 16, fontWeight: '600', color: c.textMain },
  apptProblem: { fontSize: 13, color: c.textMuted, marginTop: 2 },
  statusChip: { borderRadius: radius.full, paddingHorizontal: spacing.md, paddingVertical: 2 },
  statusText: { fontSize: 11, fontWeight: '600', textTransform: 'capitalize' },
  emptyCard: { alignItems: 'center', paddingVertical: spacing.xxl, backgroundColor: c.surface, borderRadius: radius.lg, borderWidth: 1, borderColor: c.border },
  emptyText: { fontSize: 14, color: c.textMuted, marginTop: spacing.sm },
});
