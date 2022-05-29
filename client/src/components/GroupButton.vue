<template>
  <a v-on:click="getGroup" class="navbar-item">Groupe {{
      group_name
  }}</a>
</template>

<script>
export default {
  name: 'GroupButton',
  props: {
    group_name: String,
  },
  methods: {
    getGroup() {
      this.$router.push(`/groups/${this.group_name}`);
    },
  },
};
</script>
