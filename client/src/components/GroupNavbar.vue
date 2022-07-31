<template>
  <aside class="menu">
    <p class="menu-label">
      Groupes
    </p>
    <ul class="menu-list">
      <li>
        <GroupButton v-for="groupName in groupsNames" :groupDescription="groupName['description']"></GroupButton>
      </li>
    </ul>
    <p class="menu-label">
      Classement
    </p>
    <ul class="menu-list">
      <li>
        <ScoreBoardButton />
      </li>
    </ul>
  </aside>
</template>

<script>
import GroupButton from './GroupButton.vue';
import ScoreBoardButton from './ScoreBoardButton.vue';

export default {
  name: 'GroupNavbar',
  components: {
    GroupButton,
    ScoreBoardButton,
  },
  data() {
    return {
      groupsNames: [],
    };
  },
  methods: {
    getGroupList() {
      this.$store.dispatch('getGroupNames')
        .then((res) => {
          this.groupsNames = res.data.result;
        });
    },
  },
  created() {
    this.getGroupList();
  },
};
</script>
