<template>
  <div>
    <nav class="navbar">
      <div class="container">
        <div id="navbarMenu" class="navbar-menu">
          <div class="navbar">
            <GroupButton v-for="groupName in groupsNames" :groupName="groupName"></GroupButton>
            <ScoreBoardButton />
          </div>
        </div>
      </div>
    </nav>
  </div>
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
          this.groupsNames = res.data;
        });
    },
  },
  created() {
    this.getGroupList();
  },
};
</script>
