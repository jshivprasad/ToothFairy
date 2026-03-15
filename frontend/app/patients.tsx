import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, FlatList, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../src/api';
import { colors, spacing, radius } from '../src/theme';

const c = colors.light;

export default function PatientsScreen() {
  const [patients, setPatients] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadPatients(); }, []);

  async function loadPatients() {
    try {
      const data = await api.getPatients();
      setPatients(data);
    } catch (e) {
      console.log('Error:', e);
    } finally {
      setLoading(false);
    }
  }

  const renderItem = ({ item }: any) => (
    <View testID={`patient-${item.id}`} style={styles.card}>
      <View style={styles.avatar}>
        <Text style={styles.avatarText}>{item.name?.charAt(0) || 'P'}</Text>
      </View>
      <View style={styles.info}>
        <Text style={styles.name}>{item.name}</Text>
        <Text style={styles.phone}>{item.phone}</Text>
        {item.age > 0 && <Text style={styles.meta}>{item.age} yrs • {item.gender || 'N/A'}</Text>}
      </View>
      <TouchableOpacity testID={`call-patient-${item.id}`} style={styles.callBtn}>
        <Ionicons name="call-outline" size={20} color={c.primary} />
      </TouchableOpacity>
    </View>
  );

  if (loading) {
    return <View style={styles.loadingView}><ActivityIndicator size="large" color={c.primary} /></View>;
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={patients}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="people-outline" size={48} color={c.textMuted} />
            <Text style={styles.emptyText}>No patients yet</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: c.background },
  loadingView: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: c.background },
  list: { padding: spacing.xl, paddingBottom: 100 },
  card: { flexDirection: 'row', alignItems: 'center', backgroundColor: c.surface, borderRadius: radius.lg, padding: spacing.lg, marginBottom: spacing.md, borderWidth: 1, borderColor: c.border },
  avatar: { width: 44, height: 44, borderRadius: 22, backgroundColor: c.secondary, alignItems: 'center', justifyContent: 'center', marginRight: spacing.md },
  avatarText: { fontSize: 18, fontWeight: '600', color: c.primary },
  info: { flex: 1 },
  name: { fontSize: 16, fontWeight: '600', color: c.textMain },
  phone: { fontSize: 14, color: c.textMuted, marginTop: 2 },
  meta: { fontSize: 12, color: c.textMuted, marginTop: 2 },
  callBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: c.secondary, alignItems: 'center', justifyContent: 'center' },
  empty: { alignItems: 'center', paddingTop: spacing.xxxl },
  emptyText: { fontSize: 16, color: c.textMuted, marginTop: spacing.lg },
});
